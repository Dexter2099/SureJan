"""Core application views."""

import random
import secrets
import string
import hashlib
import json
import logging
from types import SimpleNamespace
from datetime import timedelta

import bleach
import mistune
from django.utils.safestring import mark_safe

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required
from django_ratelimit.decorators import ratelimit
from django.template.loader import render_to_string
from django.conf import settings

from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db import DataError, IntegrityError
from django.db.models import F
from django import forms
from django.core.exceptions import ValidationError, RequestDataTooBig
from django.core.paginator import EmptyPage, Paginator
from django.core.validators import MaxLengthValidator

from django.core.cache import cache
from django.utils.cache import patch_cache_control

from django.contrib.contenttypes.models import ContentType
from django_ratelimit.core import is_ratelimited
from django.urls import reverse
from .forms import PostForm, CommunityCreateForm
from .models import Community, Post, RecoveryCode, Report
from comments.models import Comment
from .pagination import PAGE_SIZE
from .services.astro import compute_post_signals, compute_user_post_summary
from .services.feed import TAB_ORDER, RANGE_MAP, feed_queryset
from . import mod
from .http import login_required_htmx


logger = logging.getLogger(__name__)


def disallowed_host(request, exception=None):
    """Render a friendly message for disallowed host errors."""
    return HttpResponseBadRequest("Unknown host—check the URL")


def _error_template(request, code):
    """Return full or HTMX partial error template path."""
    if request.headers.get("HX-Request") == "true":
        return f"errors/partials/{code}.html"
    return f"errors/{code}.html"


def handler400(request, exception=None):
    """Render 400 Bad Request page."""
    return render(request, _error_template(request, 400), status=400)


def handler403(request, exception=None):
    """Render 403 Forbidden page."""
    return render(request, _error_template(request, 403), status=403)


def handler404(request, exception=None):
    """Render 404 Not Found page."""
    return render(request, _error_template(request, 404), status=404)


def handler500(request):
    """Render 500 Server Error page."""
    return render(request, _error_template(request, 500), status=500)


def handler429(request, exception=None):
    """Render 429 Too Many Requests page."""
    return render(request, _error_template(request, 429), status=429)


def request_too_big(request, exception: RequestDataTooBig | None = None):
    """Render 413 Request Entity Too Large page."""
    return render(request, _error_template(request, 413), status=413)


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


def _find_offending_field(form):
    for name, field in form.fields.items():
        value = form.data.get(name)
        if value is None:
            continue
        try:
            length = len(value)
        except TypeError:
            continue
        maxlen = getattr(field, "max_length", None)
        if maxlen and length > maxlen:
            return name, length
        for validator in field.validators:
            if isinstance(validator, MaxLengthValidator) and length > validator.limit_value:
                return name, length
    return "unknown", 0


markdown_renderer = mistune.create_markdown()
ALLOWED_TAGS = [
    "p",
    "h1",
    "h2",
    "h3",
    "a",
    "strong",
    "em",
    "code",
    "pre",
    "ul",
    "ol",
    "li",
    "blockquote",
    "br",
]
ALLOWED_ATTRIBUTES = {"a": ["href"]}


@require_GET
@ratelimit(key="user", rate="5/m", method=["GET"], block=False)
def preview_markdown(request):
    """Render sanitized markdown for body or caption preview."""
    text = request.GET.get("body", "").strip() or request.GET.get("caption", "").strip()
    html = markdown_renderer(text)
    clean = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    return render(request, "core/partials/preview.html", {"html": mark_safe(clean)})


@require_GET
@ratelimit(key="user", rate="5/m", method=["GET"], block=False)
def markdown_preview(request):
    """Return sanitized HTML fragment for provided markdown text."""
    text = request.GET.get("q", "").strip() or request.GET.get("text", "").strip()
    html = markdown_renderer(text)
    clean = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    return HttpResponse(clean)


def mission(request):
    return render(request, "core/mission.html")


def anti_astroturf(request):
    return render(request, "pages/anti_astroturf.html")


@staff_member_required
def mod_astro(request):
    """List posts with high astroturf scores for moderators."""
    posts = (
        Post.objects.filter(
            astro_score__score__gte=settings.ASTRO_BAND_RED, is_deleted=False
        )
        .select_related("community", "author", "astro_score")
        .order_by("-astro_score__score")
    )
    return render(request, "core/mod_astro.html", {"posts": posts})


def transparency_methods(request):
    if not settings.ASTROTURF_WATCH:
        raise Http404
    ctx = {
        "ASTRO_WINDOW_S": settings.ASTRO_WINDOW_S,
        "ASTRO_BUCKET_S": settings.ASTRO_BUCKET_S,
        "ASTRO_BASELINE_LOOKBACK_D": settings.ASTRO_BASELINE_LOOKBACK_D,
        "ASTRO_NEW_ACCOUNT_DAYS": settings.ASTRO_NEW_ACCOUNT_DAYS,
        "ASTRO_EARLY_VOTES_N": settings.ASTRO_EARLY_VOTES_N,
        "ASTRO_MIN_EARLY_VOTES": settings.ASTRO_MIN_EARLY_VOTES,
        "ASTRO_EARLY_SHARE_RED_PCT": int(settings.ASTRO_EARLY_SHARE_RED * 100),
        "ASTRO_BAND_AMBER": settings.ASTRO_BAND_AMBER,
        "ASTRO_BAND_RED": settings.ASTRO_BAND_RED,
        "ASTRO_SLOWMODE_THRESHOLD": settings.ASTRO_SLOWMODE_THRESHOLD,
        "ASTRO_SLOWMODE_RATE": settings.ASTRO_SLOWMODE_RATE,
    }
    return render(request, "core/transparency_methods.html", ctx)


def transparency_posts(request):
    if not settings.ASTROTURF_WATCH:
        raise Http404
    since = timezone.now() - timedelta(hours=24)
    posts = (
        Post.objects.filter(created_at__gte=since, is_deleted=False)
        .select_related("community", "author")
    )
    rows = []
    for post in posts:
        metrics = compute_post_signals(post.pk)
        if not any(metrics["flags"].values()):
            continue
        rows.append(
            {
                "post": post,
                "author_age": (timezone.now() - post.author.date_joined).days,
                "rate5": metrics["rate5"],
                "rate15": metrics["rate15"],
                "base5": metrics["thresholds"].get("p95_votes_5m", 0),
                "base15": metrics["thresholds"].get("p95_votes_15m", 0),
                "early_new_share_pct": metrics["early_new_share"] * 100.0,
                "discuss_ratio": metrics["discuss_ratio"],
                "severity": metrics["severity"],
            }
        )
    sort = request.GET.get("sort", "-severity")
    reverse = sort.startswith("-")
    key = sort.lstrip("-")
    rows.sort(key=lambda x: x.get(key, 0), reverse=reverse)

    paginator = Paginator(rows, 20)
    page_param = request.GET.get("page", "1")
    try:
        requested = int(page_param)
    except (TypeError, ValueError):
        messages.error(request, "Invalid page number.")
        return redirect(request.path)
    if requested < 1:
        messages.error(request, "Invalid page number.")
        return redirect(request.path)
    page = max(1, min(requested, paginator.num_pages))
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    ctx = {"page_obj": page_obj, "sort": sort}
    return render(request, "core/transparency_posts.html", ctx)


def _cached_post_signals(pk):
    cache_key = f"post-signals:{pk}"
    data = cache.get(cache_key)
    if data is None:
        data = compute_post_signals(pk)
        cache.set(cache_key, data, 30)
    return data




@require_GET
def post_signals_json(request, pk):
    if not settings.ASTROTURF_WATCH:
        raise Http404
    try:
        data = _cached_post_signals(pk)
    except Post.DoesNotExist:
        raise Http404
    body = json.dumps(data)
    etag = hashlib.md5(body.encode()).hexdigest()
    if request.headers.get("If-None-Match") == etag:
        return HttpResponse(status=304)
    response = HttpResponse(body, content_type="application/json")
    response["ETag"] = etag
    patch_cache_control(response, max_age=30)
    return response


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


@require_POST
def render_preview(request):
    text = request.POST.get("text", "")
    html = markdown_renderer(text)
    clean = bleach.clean(
        html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True
    )
    return render(
        request, "core/partials/preview.html", {"html": mark_safe(clean)}
    )


@login_required
@require_POST
def regenerate_recovery_codes(request):
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")
    codes = _gen_codes()
    _store_codes(request.user, codes)
    request.session["new_recovery_codes"] = codes
    return redirect("recovery_codes")


SORT_TABS = [
    ("hot", "HOT"),
    ("new", "NEW"),
    ("top", "TOP"),
    ("wiki", "WIKI"),
]


def _render_posts(request, posts, next_page, show_community=False, sort_query=""):
    """Render a list of posts and optional pagination link."""

    html = render_to_string(
        "core/partials/post_list.html",
        {
            "posts": posts,
            "show_community": show_community,
            "next_page": next_page,
            "sort_query": sort_query,
        },
        request=request,
    )
    return HttpResponse(html)


@require_GET
def feed_list(request):
    """Render the feed list or the full feed page."""
    tab = request.GET.get("tab", "hot")
    if tab not in TAB_ORDER:
        tab = "hot"

    t = request.GET.get("t")
    allowed = {"24h", "7d", "all"}
    if tab != "top" or t not in allowed:
        t = None
    if tab == "top" and t is None:
        t = "all"

    if request.headers.get("HX-Request") == "true":
        page_param = request.GET.get("page", "1")
        try:
            requested = int(page_param)
        except (TypeError, ValueError):
            messages.error(request, "Invalid page number.")
            return redirect(request.path)
        if requested < 1:
            messages.error(request, "Invalid page number.")
            return redirect(request.path)
        size = int(request.GET.get("size", PAGE_SIZE) or PAGE_SIZE)
        base_qs = Post.objects.filter(is_deleted=False).select_related("community", "author")
        qs = feed_queryset(tab, t, base_qs=base_qs)
        paginator = Paginator(qs, size)
        page = max(1, min(requested, paginator.num_pages))
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        posts = list(page_obj.object_list)
        ctx = {
            "posts": posts,
            "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
            "tab": tab,
            "t": t,
        }
        return render(request, "core/partials/feed_list.html", ctx)

    ctx = {"tab": tab, "t": t}
    return render(request, "core/feed.html", ctx)


@require_GET
def home(request):
    """Render the front page with optional sorting and time filters."""
    sort = request.GET.get("sort", "hot")
    if sort not in TAB_ORDER:
        sort = "hot"

    t = request.GET.get("t")
    allowed = {"24h", "7d", "all"}
    if sort != "top" or t not in allowed:
        t = None
    if sort == "top" and t is None:
        t = "all"

    page = int(request.GET.get("page", "1") or 1)
    base_qs = Post.objects.filter(is_deleted=False).select_related("community", "author")
    qs = feed_queryset(sort, t, base_qs=base_qs)
    offset = (page - 1) * PAGE_SIZE
    posts = list(qs[offset : offset + PAGE_SIZE + 1])
    next_page = page + 1 if len(posts) > PAGE_SIZE else None
    posts = posts[:PAGE_SIZE]

    sort_query = ""
    if sort and sort != "hot":
        sort_query += f"&sort={sort}"
    if sort == "top" and t:
        sort_query += f"&t={t}"

    if request.headers.get("HX-Request") == "true":
        return _render_posts(request, posts, next_page, show_community=True, sort_query=sort_query)

    ctx = {
        "posts": posts,
        "next_page": next_page,
        "sort_query": sort_query,
        "sort": sort,
        "t": t,
        "sort_tabs": SORT_TABS,
    }
    return render(request, "core/home.html", ctx)


@ratelimit(key="user", rate="5/m", method=["POST"], block=False)
@require_http_methods(["GET", "POST"])
def post_submit(request):
    """Handle post submission, redirecting unauthenticated users to login."""

    if not request.user.is_authenticated:
        if request.method == "POST":
            request.session["post_data"] = request.POST.dict()
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")

    initial = request.session.pop("post_data", None)
    if initial and "link" in initial:
        initial["content_url"] = initial.pop("link")
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if is_new_user(request.user):
            limited = limit_or_429(request, "post_new_user", "3/m")
        else:
            limited = limit_or_429(request, "post_established", "10/m")
        if limited:
            form.add_error(
                None, "You're posting too fast. Please wait before trying again."
            )
            return render(request, "core/submit.html", {"form": form}, status=429)
        if form.is_valid():
            post_type = form.cleaned_data["post_type"]
            post = Post(
                community=form.cleaned_data["community"],
                author=request.user,
                post_type=post_type,
                title=form.cleaned_data["title"],
                body=form.cleaned_data.get("body", ""),
            )

            if post_type == "image":
                image = form.cleaned_data.get("image")
                if image:
                    post.image = image
                else:
                    post.content_url = form.cleaned_data.get("content_url", "")
            elif post_type == "link":
                post.content_url = form.cleaned_data.get("content_url", "")
            try:
                post.save()
            except (DataError, IntegrityError):
                field, size = _find_offending_field(form)
                logger.error("path=%s field=%s size=%s", request.path, field, size)
                form.add_error(
                    None, "One or more fields exceed the allowed length."
                )
                return render(request, "core/submit.html", {"form": form}, status=400)
            messages.success(request, "Post submitted")
            return redirect(
                "post_detail",
                community=post.community.slug,
                pk=post.pk,
                slug=post.slug,
            )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PostForm(initial=initial)

    return render(request, "core/submit.html", {"form": form})


@require_GET
def communities_index(request):
    """List available communities."""
    sort = request.GET.get("sort", "hot")
    if sort not in TAB_ORDER:
        sort = "hot"

    t = request.GET.get("t")
    allowed = {"24h", "7d", "all"}
    if sort != "top" or t not in allowed:
        t = None
    if sort == "top" and t is None:
        t = "all"

    communities = [
        {"slug": "news", "name": "News"},
        {"slug": "brisbane", "name": "Brisbane"},
        {"slug": "history", "name": "History"},
        {"slug": "politics", "name": "Politics"},
        {"slug": "social", "name": "Social"},
    ]

    qs = ""
    if sort != "hot":
        qs = f"?sort={sort}"
        if sort == "top" and t and t != "all":
            qs += f"&t={t}"

    ctx = {"communities": communities, "qs": qs, "sort": sort, "t": t}
    return render(request, "core/communities_index.html", ctx)


def community(request, slug):
    """Display posts for a specific community."""
    try:
        community = Community.objects.get(slug=slug)
    except Community.DoesNotExist:
        return redirect("/")
    sort = request.GET.get("sort", "hot")
    if sort not in TAB_ORDER:
        sort = "hot"

    t = request.GET.get("t")
    allowed = {"24h", "7d", "all"}
    if sort != "top" or t not in allowed:
        t = None
    if sort == "top" and t is None:
        t = "all"

    page_param = request.GET.get("page", "1")
    try:
        requested = int(page_param)
    except (TypeError, ValueError):
        messages.error(request, "Invalid page number.")
        return redirect(request.path)
    if requested < 1:
        messages.error(request, "Invalid page number.")
        return redirect(request.path)

    base_qs = community.posts.filter(is_deleted=False).select_related("author")
    qs = feed_queryset(sort, t, base_qs=base_qs)

    paginator = Paginator(qs, PAGE_SIZE)
    page = max(1, min(requested, paginator.num_pages))
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    posts = list(page_obj.object_list)
    next_page = page_obj.next_page_number() if page_obj.has_next() else None

    sort_query = ""
    if sort and sort != "hot":
        sort_query += f"&sort={sort}"
    if sort == "top" and t:
        sort_query += f"&t={t}"

    if request.headers.get("HX-Request") == "true":
        return _render_posts(request, posts, next_page, sort_query=sort_query)

    context = {
        "community": community,
        "community_slug": community.slug,
        "posts": posts,
        "next_page": next_page,
        "sort_query": sort_query,
        "sort": sort,
        "t": t,
        "sort_tabs": SORT_TABS,
    }
    return render(request, "core/community.html", context)




def post_detail(request, community, pk, slug):
    """Display a single post and its comments."""

    post = get_object_or_404(
        Post.objects.filter(is_deleted=False),
        pk=pk,
        community__slug=community,
    )
    c_sort = request.GET.get("c_sort", "best")
    q = request.GET.get("q", "").strip()
    if c_sort not in {"best", "top", "new", "controversial"}:
        c_sort = "best"

    comments = (
        post.comments.filter(parent__isnull=True)
        .select_related("author")
        .prefetch_related("children__author")
    )
    if q:
        comments = comments.filter(body__icontains=q)

    if c_sort == "top":
        comments = comments.order_by("-score", "-created_at")
    elif c_sort == "new":
        comments = comments.order_by("-created_at")
    elif c_sort == "controversial":
        comments = comments.order_by(F("score").abs().desc(), "-created_at")
    else:  # best
        comments = comments.order_by("-score", "path")

    severity = None
    band = None
    try:
        severity = getattr(getattr(post, "astro_score", None), "severity", None)
    except Exception:
        severity = None
    if severity is None:
        try:
            metrics = compute_post_signals(post.pk)
            severity = metrics.get("severity")
        except Exception:
            severity = None

    if isinstance(severity, (int, float)):
        if severity < 40:
            band = "green"
        elif severity < 70:
            band = "amber"
        else:
            band = "red"

    context = {
        "post": post,
        "comments": comments,
        "c_sort": c_sort,
        "q": q,
        "severity": severity,
        "severity_band": band,
    }
    return render(request, "core/post_detail.html", context)


def post_detail_id(request, pk):
    """Simpler post detail view addressed by ID only."""

    post = get_object_or_404(
        Post.objects.filter(is_deleted=False),
        pk=pk,
    )
    c_sort = request.GET.get("c_sort", "best")
    q = request.GET.get("q", "").strip()
    if c_sort not in {"best", "top", "new", "controversial"}:
        c_sort = "best"

    comments = (
        post.comments.filter(parent__isnull=True)
        .select_related("author")
        .prefetch_related("children__author")
    )
    if q:
        comments = comments.filter(body__icontains=q)

    if c_sort == "top":
        comments = comments.order_by("-score", "-created_at")
    elif c_sort == "new":
        comments = comments.order_by("-created_at")
    elif c_sort == "controversial":
        comments = comments.order_by(F("score").abs().desc(), "-created_at")
    else:  # best
        comments = comments.order_by("-score", "path")

    severity = None
    band = None
    try:
        severity = getattr(getattr(post, "astro_score", None), "severity", None)
    except Exception:
        severity = None
    if severity is None:
        try:
            metrics = compute_post_signals(post.pk)
            severity = metrics.get("severity")
        except Exception:
            severity = None

    if isinstance(severity, (int, float)):
        if severity < 40:
            band = "green"
        elif severity < 70:
            band = "amber"
        else:
            band = "red"

    context = {
        "post": post,
        "comments": comments,
        "c_sort": c_sort,
        "q": q,
        "severity": severity,
        "severity_band": band,
    }
    return render(request, "core/post_detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def post_edit(request, pk):
    post = get_object_or_404(Post.objects.filter(is_deleted=False), pk=pk)
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")
    if request.user != post.author and not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")

    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            messages.success(request, "Post updated")
            return redirect(
                "post_detail",
                community=post.community.slug,
                pk=post.pk,
                slug=post.slug,
            )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PostForm(instance=post)

    context = {"form": form, "community": post.community, "post": post}
    return render(request, "core/post_form.html", context)


@require_POST
@csrf_protect
def post_delete_owner(request, pk):
    post = get_object_or_404(Post.objects.filter(is_deleted=False), pk=pk)
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")

    if request.user != post.author and not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")

    post.soft_delete(request.user)

    if request.headers.get("HX-Request") == "true":
        if request.POST.get("from") == "detail":
            resp = HttpResponse("", content_type="text/html")
            resp["HX-Redirect"] = reverse("community", args=[post.community.slug])
            return resp
        return HttpResponse("", content_type="text/html")
    return redirect("community", slug=post.community.slug)


@require_POST
@csrf_protect
def post_delete(request, pk):
    """Hard delete a post.

    This view is intended for administrative use only and isn't linked from the
    standard user interface. Only staff members may perform this action.
    """
    if not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")
    post = get_object_or_404(Post.objects.filter(is_deleted=False), pk=pk)
    slug = post.community.slug
    post.delete()
    return redirect("community", slug=slug)


@login_required
@require_POST
@csrf_protect
def post_remove(request, pk):
    """Soft delete a post (moderator remove)."""
    if not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")
    post = get_object_or_404(Post.objects.filter(is_deleted=False), pk=pk)
    mod.remove_post(post, request.user)
    if request.headers.get("HX-Request") == "true":
        html = render_to_string("core/partials/post_deleted_stub.html", {"post": post})
        return HttpResponse(html)
    return redirect(
        "post_detail",
        community=post.community.slug,
        pk=post.id,
        slug=post.slug,
    )


@login_required
@require_POST
@csrf_protect
def post_lock(request, pk):
    """Lock or unlock a post's comments."""
    if not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")
    post = get_object_or_404(Post.objects.filter(is_deleted=False), pk=pk)
    state = request.POST.get("state")
    mod.lock_post(post, state == "1")
    html = render_to_string("core/partials/mod_controls.html", {"post": post}, request=request)
    return HttpResponse(html)


@login_required
@require_POST
@csrf_protect
def post_slowmode(request, pk):
    """Adjust per-post slowmode comment rate."""
    if not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")
    post = get_object_or_404(Post.objects.filter(is_deleted=False), pk=pk)
    try:
        seconds = int(request.POST.get("seconds", 0))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid value")
    if seconds not in {0, 30, 60, 120}:
        return HttpResponseBadRequest("Invalid value")
    post.slowmode = seconds
    post.save(update_fields=["slowmode"])
    html = render_to_string("core/partials/mod_controls.html", {"post": post}, request=request)
    return HttpResponse(html)


@login_required
@require_POST
@csrf_protect
def post_domain_throttle(request, pk):
    """Toggle domain throttling (-50% weight) for a post."""
    if not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")
    post = get_object_or_404(Post.objects.filter(is_deleted=False), pk=pk)
    state = request.POST.get("state")
    if state not in {"0", "1"}:
        return HttpResponseBadRequest("Invalid value")
    mod.set_domain_throttle(post.link_domain, state == "1")
    post.refresh_from_db()
    html = render_to_string("core/partials/mod_controls.html", {"post": post}, request=request)
    return HttpResponse(html)

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
        mode = request.POST.get("mode")
    else:
        target_type = request.GET.get("target_type")
        object_id = request.GET.get("object_id")
        mode = request.GET.get("mode")

    is_note = mode == "note"
    if is_note and not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")

    if target_type not in {"post", "comment"}:
        return HttpResponseBadRequest("Invalid target")

    try:
        object_id = int(object_id)
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid object id")

    model = Post if target_type == "post" else Comment
    target_qs = model.objects.filter(is_deleted=False) if model is Post else model.objects.all()
    target = get_object_or_404(target_qs, pk=object_id)

    if request.method == "POST":
        reason = request.POST.get("reason", "")
        Report.objects.create(
            reporter=request.user,
            content_type=ContentType.objects.get_for_model(target),
            object_id=target.pk,
            reason=reason,
            is_note=is_note,
        )
        return render(request, "core/report_form.html", {"thanks": True, "mode": mode})

    return render(
        request,
        "core/report_form.html",
        {"target": target, "target_type": target_type, "object_id": object_id, "mode": mode},
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
