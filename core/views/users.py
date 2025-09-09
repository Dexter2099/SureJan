"""User-related views."""

import random
import secrets
import string

from django import forms
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.views import LoginView
from django.core.validators import MaxLengthValidator
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from ..models import Post, RecoveryCode
from comments.models import Comment
from core.services import compute_user_post_summary
from ..utils.view_helpers import _is_banned


class SignupForm(forms.Form):
    username = forms.CharField(
        max_length=191, validators=[MaxLengthValidator(191)]
    )
    password = forms.CharField(widget=forms.PasswordInput)
    captcha = forms.IntegerField(required=False)


class RateLimitedLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def _ensure_captcha(self, request):
        a = random.randint(1, 9)
        b = random.randint(1, 9)
        request.session["captcha_q"] = (a, b)
        return f"{a} + {b} = ?"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        fails = self.request.session.get("login_fails", 0)
        if fails >= 5 and "captcha_q" not in self.request.session:
            self._ensure_captcha(self.request)
        if fails >= 5 and "captcha_q" in self.request.session:
            a, b = self.request.session["captcha_q"]
            ctx["captcha_question"] = f"{a} + {b} = ?"
        ctx["login_fails"] = fails
        return ctx

    @method_decorator(ratelimit(key="ip", rate="10/m", block=False))
    @method_decorator(ratelimit(key="post:username", rate="10/m", block=False))
    def dispatch(self, request, *args, **kw):
        return super().dispatch(request, *args, **kw)

    def form_valid(self, form):
        self.request.session.pop("captcha_q", None)
        self.request.session["login_fails"] = 0
        return super().form_valid(form)

    def form_invalid(self, form):
        fails = self.request.session.get("login_fails", 0) + 1
        self.request.session["login_fails"] = fails
        if fails >= 5:
            a, b = self.request.session.get("captcha_q", (None, None))
            answer = self.request.POST.get("captcha", "").strip()
            if a is None or b is None:
                self._ensure_captcha(self.request)
                form.add_error(None, "Please answer the captcha.")
                return super().form_invalid(form)
            try:
                if int(answer) != (a + b):
                    self._ensure_captcha(self.request)
                    form.add_error(None, "Captcha answer was incorrect.")
                    return super().form_invalid(form)
            except ValueError:
                form.add_error(None, "Captcha answer was incorrect.")
                return super().form_invalid(form)
        return super().form_invalid(form)


@ratelimit(key="ip", rate="5/m", block=False)
def signup(request):
    """Create a new user account and log them in."""

    def _ensure_captcha(req):
        a = random.randint(1, 9)
        b = random.randint(1, 9)
        req.session["signup_captcha_q"] = (a, b)
        return f"{a} + {b} = ?"

    if request.method == "POST":
        if getattr(request, "limited", False):
            resp = HttpResponse("Too many requests", status=429)
            resp.headers["X-RateLimit-Triggered"] = "1"
            return resp
        form = SignupForm(request.POST)
        a, b = request.session.get("signup_captcha_q", (None, None))
        if a is None or b is None:
            captcha_q = _ensure_captcha(request)
        else:
            captcha_q = f"{a} + {b} = ?"
        if form.is_valid():
            try:
                if int(request.POST.get("captcha", "")) != a + b:
                    form.add_error("captcha", "Captcha answer was incorrect.")
                else:
                    U = get_user_model()
                    username = form.cleaned_data["username"]
                    if U.objects.filter(username=username).exists():
                        form.add_error("username", "That username is taken.")
                    else:
                        user = U.objects.create_user(
                            username=username, password=form.cleaned_data["password"]
                        )
                        login(request, user)
                        codes = _gen_codes()
                        _store_codes(user, codes)
                        request.session["new_recovery_codes"] = codes
                        return redirect("recovery_codes")
            except (TypeError, ValueError):
                form.add_error("captcha", "Captcha answer was incorrect.")
    else:
        form = SignupForm()
        captcha_q = _ensure_captcha(request)
    if request.method != "POST" or not form.is_valid():
        if "signup_captcha_q" not in request.session:
            captcha_q = _ensure_captcha(request)
    return render(
        request,
        "registration/signup.html",
        {"form": form, "captcha_question": captcha_q},
    )


def _gen_codes(n=8, length=10):
    alphabet = string.ascii_uppercase + string.digits
    return ["".join(secrets.choice(alphabet) for _ in range(length)) for _ in range(n)]


def _store_codes(user, codes):
    RecoveryCode.objects.filter(user=user).delete()
    RecoveryCode.objects.bulk_create(
        [RecoveryCode(user=user, code_hash=make_password(c)) for c in codes]
    )


@login_required
def recovery_codes(request):
    codes = request.session.get("new_recovery_codes")
    if not codes:
        return HttpResponseForbidden("No recovery codes available.")
    request.session["download_recovery_codes"] = codes
    request.session.pop("new_recovery_codes", None)
    return render(request, "accounts/recovery_codes.html", {"codes": codes})


@login_required
def download_recovery_codes(request):
    codes = request.session.pop("download_recovery_codes", None)
    if not codes:
        return HttpResponseForbidden("No recovery codes available.")
    resp = HttpResponse("\n".join(codes), content_type="text/plain")
    resp["Content-Disposition"] = "attachment; filename=recovery-codes.txt"
    return resp


@login_required
@require_POST
def regenerate_recovery_codes(request):
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")
    codes = _gen_codes()
    _store_codes(request.user, codes)
    request.session["new_recovery_codes"] = codes
    return redirect("recovery_codes")


def _get_profile_user(username):
    """Return the user object for the given username or 404."""

    return get_object_or_404(get_user_model(), username=username)


def user_overview(request, username):
    """Display recent activity for a user."""

    profile_user = _get_profile_user(username)
    posts = list(
        Post.objects.filter(author=profile_user, is_deleted=False)
        .select_related("community")
        .order_by("-created_at")[:10]
    )
    comments = list(
        Comment.objects.filter(author=profile_user)
        .select_related("post__community")
        .order_by("-created_at")[:10]
    )

    activity = [
        {"type": "post", "obj": p, "created_at": p.created_at} for p in posts
    ] + [
        {"type": "comment", "obj": c, "created_at": c.created_at} for c in comments
    ]
    activity.sort(key=lambda a: a["created_at"], reverse=True)
    activity = activity[:20]

    summary = compute_user_post_summary(profile_user.id)

    context = {
        "profile_user": profile_user,
        "activity": activity,
        "tab": "overview",
        "user_summary": summary,
    }
    return render(request, "core/user_overview.html", context)


def user_comments(request, username):
    """Display all comments made by a user."""

    profile_user = _get_profile_user(username)
    comments = (
        Comment.objects.filter(author=profile_user)
        .select_related("post__community")
        .order_by("-created_at")
    )
    context = {
        "profile_user": profile_user,
        "comments": comments,
        "tab": "comments",
    }
    return render(request, "core/user_comments.html", context)


def user_submitted(request, username):
    """Display all posts submitted by a user."""

    profile_user = _get_profile_user(username)
    posts = (
        Post.objects.filter(author=profile_user, is_deleted=False)
        .select_related("community")
        .order_by("-created_at")
    )
    context = {
        "profile_user": profile_user,
        "posts": posts,
        "tab": "submitted",
    }
    return render(request, "core/user_submitted.html", context)


@login_required
@require_POST
@csrf_protect
def ban_user(request, username):
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")
    if not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")
    user = _get_profile_user(username)
    if user == request.user:
        return HttpResponseForbidden("Cannot modify yourself")
    user.profile.is_banned = True
    user.profile.save(update_fields=["is_banned"])
    return redirect("user_overview", username=username)


@login_required
@require_POST
@csrf_protect
def unban_user(request, username):
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")
    if not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")
    user = _get_profile_user(username)
    user.profile.is_banned = False
    user.profile.save(update_fields=["is_banned"])
    return redirect("user_overview", username=username)
