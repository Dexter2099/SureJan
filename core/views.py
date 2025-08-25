"""Core application views."""

import random
import secrets
import string
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required
from django_ratelimit.decorators import ratelimit
from django.template.loader import render_to_string

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import F
from django import forms

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import connections
from django_ratelimit.core import is_ratelimited

from .forms import CommentForm, PostForm, CommunityCreateForm
from .models import Comment, Community, Post, RecoveryCode, Report
from .votes import apply_vote
from .pagination import PAGE_SIZE


def _is_banned(user):
    return getattr(getattr(user, "profile", None), "is_banned", False)


def is_new_user(u):
    if not u.is_authenticated:
        return True
    return (timezone.now() - u.date_joined) < timedelta(hours=24)


def limit_or_429(request, group, rate):
    return is_ratelimited(
        request,
        group=group,
        key="user",
        rate=rate,
        method=["POST"],
        increment=True,
    )


def healthz(_request):
    """Health check verifying database and cache connectivity."""
    try:
        connections["default"].cursor()
        cache.set("healthz", "ok", 1)
        cache.get("healthz")
    except Exception:
        return HttpResponse("unhealthy", status=500, content_type="text/plain")
    return HttpResponse("ok", content_type="text/plain")


def mission(request):
    return render(request, "core/mission.html")


class SignupForm(forms.Form):
    username = forms.CharField(max_length=150)
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


# Mapping of feed tabs to their ordering in the database.  Each ordering
# includes ``-id`` as the final column to guarantee deterministic results.
FEED_ORDER = {
    "best": ["-best_rank", "-created_at", "-id"],
    "hot": ["-hot_rank", "-created_at", "-id"],
    "new": ["-created_at", "-id"],
    "rising": ["-rising_rank", "-created_at", "-id"],
    "controversial": ["-controversy", "-created_at", "-id"],
    "top": ["-score", "-created_at", "-id"],
}

SORT_TABS = [
    ("best", "BEST"),
    ("hot", "HOT"),
    ("new", "NEW"),
    ("rising", "RISING"),
    ("controversial", "CONTROVERSIAL"),
    ("top", "TOP"),
    ("wiki", "WIKI"),
]


def _render_posts(request, posts, next_page, show_community=False, sort_query=""):
    """Render a list of posts and optional pagination link."""

    html = render_to_string(
        "core/partials/post_list.html",
        {"posts": posts, "show_community": show_community},
        request=request,
    )
    if next_page:
        next_url = f"{request.path}?page={next_page}{sort_query}"
        html += render_to_string(
            "core/partials/load_more.html", {"next_url": next_url}, request=request
        )
    return HttpResponse(html)


def home(request):
    """Display a feed of posts across all communities."""
    sort = request.GET.get("sort", "best")
    if sort not in FEED_ORDER:
        sort = "best"
    order = FEED_ORDER[sort]
    page = int(request.GET.get("page", "1") or 1)

    qs = Post.objects.select_related("community", "author").order_by(*order)

    offset = (page - 1) * PAGE_SIZE
    posts = list(qs[offset : offset + PAGE_SIZE + 1])
    next_page = page + 1 if len(posts) > PAGE_SIZE else None
    posts = posts[:PAGE_SIZE]

    sort_query = f"&sort={sort}" if sort and sort != "best" else ""
    context = {
        "posts": posts,
        "next_page": next_page,
        "sort_query": sort_query,
        "sort": sort,
        "sort_tabs": SORT_TABS,
    }
    if request.headers.get("HX-Request") == "true":
        return _render_posts(
            request, posts, next_page, show_community=True, sort_query=sort_query
        )
    return render(request, "core/home.html", context)


def community(request, slug):
    """Display posts for a specific community."""
    community = get_object_or_404(Community, slug=slug)
    sort = request.GET.get("sort", "best")
    if sort not in FEED_ORDER:
        sort = "best"
    order = FEED_ORDER[sort]
    page = int(request.GET.get("page", "1") or 1)

    qs = community.posts.select_related("author").order_by(*order)
    offset = (page - 1) * PAGE_SIZE
    posts = list(qs[offset : offset + PAGE_SIZE + 1])
    next_page = page + 1 if len(posts) > PAGE_SIZE else None
    posts = posts[:PAGE_SIZE]

    sort_query = f"&sort={sort}" if sort and sort != "best" else ""
    context = {
        "community": community,
        "community_slug": community.slug,
        "posts": posts,
        "next_page": next_page,
        "sort_query": sort_query,
        "sort": sort,
        "sort_tabs": SORT_TABS,
    }
    if request.headers.get("HX-Request") == "true":
        return _render_posts(request, posts, next_page, sort_query=sort_query)
    return render(request, "core/community.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def submit_post(request, slug):
    """Submit a new post to a community."""

    community = get_object_or_404(Community, slug=slug)
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")

    if request.method == "POST":
        if is_new_user(request.user):
            if limit_or_429(request, "submit_new_user", "3/m"):
                return render(request, "429.html", status=429)
        else:
            if limit_or_429(request, "submit_established", "10/m"):
                return render(request, "429.html", status=429)
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.community = community
            post.author = request.user
            post.save()
            messages.success(request, "Post submitted")
            return redirect("community", slug=community.slug)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PostForm()

    context = {"form": form, "community": community}
    return render(request, "core/submit_post.html", context)


def post_detail(request, slug, post_id, post_slug):
    """Display a single post and its comments."""

    post = get_object_or_404(Post, pk=post_id, community__slug=slug)
    comments = post.comments.select_related("author").order_by("path")
    form = CommentForm()
    context = {"post": post, "comments": comments, "form": form}
    return render(request, "core/post_detail.html", context)


@login_required
@require_POST
def comment_reply(request, post_id):
    """Create a new comment on a post or comment."""
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")

    if is_new_user(request.user):
        if limit_or_429(request, "comment_new_user", "3/m"):
            return render(request, "429.html", status=429)
    else:
        if limit_or_429(request, "comment_established", "10/m"):
            return render(request, "429.html", status=429)

    post = get_object_or_404(Post, pk=post_id)

    form = CommentForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest("Invalid comment")

    parent_id = request.POST.get("parent_id")
    parent = None
    if parent_id:
        parent = get_object_or_404(Comment, pk=parent_id, post=post)
        child_seq = parent.children.count() + 1
        path = f"{parent.path}/{child_seq:04d}"
    else:
        root_seq = post.comments.filter(parent__isnull=True).count() + 1
        path = f"{root_seq:04d}"

    comment = Comment.objects.create(
        post=post,
        author=request.user,
        parent=parent,
        body=form.cleaned_data["body"],
        path=path,
    )
    Post.objects.filter(pk=post.pk).update(comment_count=F("comment_count") + 1)

    if request.headers.get("HX-Request") == "true":
        html = render_to_string(
            "core/partials/comment.html", {"comment": comment}, request=request
        )
        return HttpResponse(html)

    return redirect(
        "post_detail",
        slug=post.community.slug,
        post_id=post.pk,
        post_slug=slugify(post.title),
    )


@login_required
@require_http_methods(["GET"])
def comment_reply_form(request, post_id):
    """Render the comment reply form via HTMX."""

    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")
    if request.headers.get("HX-Request") != "true":
        return HttpResponseBadRequest("Invalid request")

    post = get_object_or_404(Post, pk=post_id)
    parent_id = request.GET.get("parent_id")
    if not parent_id:
        return HttpResponseBadRequest("Missing parent_id")
    parent = get_object_or_404(Comment, pk=parent_id, post=post)
    form = CommentForm()
    html = render_to_string(
        "core/partials/reply_form.html",
        {"form": form, "parent": parent, "post": post},
        request=request,
    )
    return HttpResponse(html)


@require_POST
@csrf_protect
def post_delete(request, pk):
    """Delete a post; only staff members may perform this action."""
    if not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")
    post = get_object_or_404(Post, pk=pk)
    slug = post.community.slug
    post.delete()
    return redirect("community", slug=slug)


@login_required
@require_POST
@csrf_protect
def comment_delete(request, pk):
    """Delete a comment if the requester is the author or staff."""
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")

    comment = get_object_or_404(Comment, pk=pk)
    if request.user != comment.author and not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")

    post = comment.post
    # number of comments to remove including any descendants
    count = Comment.objects.filter(post=post, path__startswith=comment.path).count()
    comment.delete()
    Post.objects.filter(pk=post.pk).update(comment_count=F("comment_count") - count)

    if request.headers.get("HX-Request") == "true":
        return HttpResponse("")

    return redirect(
        "post_detail",
        slug=post.community.slug,
        post_id=post.pk,
        post_slug=slugify(post.title),
    )


@login_required
@require_POST
@csrf_protect
@ratelimit(key="user", rate="120/m", method=["POST"], block=False)
def vote_post(request, pk):
    """Handle voting on a post."""

    if getattr(request, "limited", False):
        resp = HttpResponse("Too many requests", status=429)
        resp.headers["X-RateLimit-Triggered"] = "1"
        return resp
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")

    try:
        value = int(request.GET.get("v") or request.POST.get("v"))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid vote")

    try:
        apply_vote(request.user, "post", pk, value)
    except ValueError:
        return HttpResponseBadRequest("Invalid vote")

    score = Post.objects.get(pk=pk).score
    return HttpResponse(f"<span id='post-score-{pk}'>{score}</span>")


@login_required
@require_POST
@csrf_protect
@ratelimit(key="user", rate="120/m", method=["POST"], block=False)
def vote_comment(request, pk):
    """Handle voting on a comment."""

    if getattr(request, "limited", False):
        resp = HttpResponse("Too many requests", status=429)
        resp.headers["X-RateLimit-Triggered"] = "1"
        return resp
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")

    try:
        value = int(request.GET.get("v") or request.POST.get("v"))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid vote")

    try:
        apply_vote(request.user, "comment", pk, value)
    except ValueError:
        return HttpResponseBadRequest("Invalid vote")

    score = Comment.objects.get(pk=pk).score
    return HttpResponse(f"<span id='comment-score-{pk}'>{score}</span>")


@login_required
@require_http_methods(["GET", "POST"])
@csrf_protect
def report(request):
    """Allow users to report posts or comments."""
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")

    if request.method == "POST":
        target_type = request.POST.get("target_type")
        object_id = request.POST.get("object_id")
    else:
        target_type = request.GET.get("target_type")
        object_id = request.GET.get("object_id")

    if target_type not in {"post", "comment"}:
        return HttpResponseBadRequest("Invalid target")

    try:
        object_id = int(object_id)
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid object id")

    model = Post if target_type == "post" else Comment
    target = get_object_or_404(model, pk=object_id)

    if request.method == "POST":
        reason = request.POST.get("reason", "")
        Report.objects.create(
            reporter=request.user,
            content_type=ContentType.objects.get_for_model(target),
            object_id=target.pk,
            reason=reason,
        )
        return render(request, "core/report_form.html", {"thanks": True})

    return render(
        request,
        "core/report_form.html",
        {"target": target, "target_type": target_type, "object_id": object_id},
    )


@staff_member_required
def report_list(request):
    """Simple listing view for recent reports."""
    reports = Report.objects.select_related("reporter", "content_type").order_by("-created_at")
    return render(request, "core/report_list.html", {"reports": reports})


def community_wiki(request, slug):
    """Render the community wiki if available, otherwise show a stub."""

    community = get_object_or_404(Community, slug=slug)
    context = {"community": community}
    return render(request, "core/community_wiki.html", context)


def _get_profile_user(username):
    """Return the user object for the given username or 404."""

    from django.contrib.auth import get_user_model

    return get_object_or_404(get_user_model(), username=username)


def user_overview(request, username):
    """Display recent activity for a user."""

    profile_user = _get_profile_user(username)
    posts = list(
        Post.objects.filter(author=profile_user)
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

    context = {
        "profile_user": profile_user,
        "activity": activity,
        "tab": "overview",
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
        Post.objects.filter(author=profile_user)
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


@login_required
@require_http_methods(["GET", "POST"])
@ratelimit(key="user", rate="5/m", method=["POST"], block=False)
def create_community(request):
    if not request.user.is_staff:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")
    if request.method == "POST":
        if is_ratelimited(request, group="community-create", key="user", rate="5/m", method=["POST"], increment=True):
            return HttpResponse(status=429)
        form = CommunityCreateForm(request.POST)
        if form.is_valid():
            community = form.save(commit=False)
            community.created_by = request.user
            community.save()
            return redirect("community", slug=community.slug)
    else:
        form = CommunityCreateForm()
    return render(request, "communities/create.html", {"form": form})
