"""Core application views."""

import random
import secrets
import string
import hashlib
import json
from datetime import timedelta

import re
from urllib.parse import urlparse, quote

import requests
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
from django.utils.text import slugify
from django.db.models import F
from django import forms
from django.core.paginator import Paginator

from django.core.cache import cache
from django.utils.cache import patch_cache_control

from django.contrib.contenttypes.models import ContentType
from django_ratelimit.core import is_ratelimited
from django.urls import reverse

from .forms import CommentForm, PostForm, CommunityCreateForm
from .models import Comment, Community, Post, RecoveryCode, Report
from .votes import apply_vote
from .pagination import PAGE_SIZE
from .services.astro import compute_post_signals, compute_user_post_summary


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


def fetch_oembed(url: str):
    """Fetch and sanitize oEmbed HTML for supported providers.

    If unsupported or fetch fails, return a fallback link card.
    """

    providers = {
        "youtube.com": "https://www.youtube.com/oembed?format=json&url=",
        "youtu.be": "https://www.youtube.com/oembed?format=json&url=",
        "rumble.com": "https://rumble.com/api/oembed.json?url=",
        "twitter.com": "https://publish.twitter.com/oembed?omit_script=1&url=",
        "x.com": "https://publish.twitter.com/oembed?omit_script=1&url=",
    }

    parsed = urlparse(url)
    domain = parsed.netloc
    endpoint = None
    for key, base in providers.items():
        if key in domain:
            endpoint = f"{base}{quote(url, safe='')}"
            break

    if endpoint:
        try:
            resp = requests.get(endpoint, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            html = data.get("html", "")
            clean = bleach.clean(
                html,
                tags=[
                    "iframe",
                    "blockquote",
                    "a",
                    "p",
                    "span",
                    "img",
                    "br",
                    "div",
                ],
                attributes={
                    "iframe": [
                        "src",
                        "width",
                        "height",
                        "frameborder",
                        "allow",
                        "allowfullscreen",
                    ],
                    "blockquote": ["class", "data-theme"],
                    "a": ["href", "class"],
                    "img": ["src", "alt"],
                    "div": ["class"],
                },
                strip=True,
            )
            return {"type": "embed", "html": clean}
        except Exception:
            pass

    # Fallback link card
    title = None
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        match = re.search(r"<title>(.*?)</title>", resp.text, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1).strip()
    except Exception:
        pass
    favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
    return {
        "type": "link",
        "url": url,
        "domain": domain,
        "title": title,
        "favicon": favicon,
    }


@require_POST
def oembed_preview(request):
    url = request.POST.get("url", "").strip()
    if not url:
        return HttpResponse("")
    data = fetch_oembed(url)
    html = render_to_string("core/partials/link_preview.html", data)
    return HttpResponse(html)


def mission(request):
    return render(request, "core/mission.html")


def transparency_methods(request):
    ctx = {
        "ASTRO_WINDOW_S": settings.ASTRO_WINDOW_S,
        "ASTRO_BUCKET_S": settings.ASTRO_BUCKET_S,
        "ASTRO_BASELINE_LOOKBACK_D": settings.ASTRO_BASELINE_LOOKBACK_D,
        "ASTRO_NEW_ACCOUNT_DAYS": settings.ASTRO_NEW_ACCOUNT_DAYS,
        "ASTRO_EARLY_VOTES_N": settings.ASTRO_EARLY_VOTES_N,
        "ASTRO_MIN_EARLY_VOTES": settings.ASTRO_MIN_EARLY_VOTES,
        "ASTRO_EARLY_SHARE_RED_PCT": int(settings.ASTRO_EARLY_SHARE_RED * 100),
    }
    return render(request, "core/transparency_methods.html", ctx)


def transparency_posts(request):
    since = timezone.now() - timedelta(hours=24)
    posts = (
        Post.objects.filter(created_at__gte=since)
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
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

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


@require_GET
def post_signals_chips(request, pk):
    try:
        data = _cached_post_signals(pk)
    except Post.DoesNotExist:
        raise Http404
    response = render(
        request,
        "core/partials/post_context_chips.html",
        {"signals": data},
    )
    etag = hashlib.md5(response.content).hexdigest()
    if request.headers.get("If-None-Match") == etag:
        return HttpResponse(status=304)
    response["ETag"] = etag
    patch_cache_control(response, max_age=30)
    return response


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


@require_POST
def render_preview(request):
    text = request.POST.get("text", "")
    html = markdown_renderer(text)
    clean = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
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


def comment_children(request):
    """Return a batch of child comments for progressive loading."""

    if request.headers.get("HX-Request") != "true":
        return HttpResponseBadRequest("Invalid request")

    parent_id = request.GET.get("parent")
    if not parent_id:
        return HttpResponseBadRequest("Missing parent")

    try:
        offset = int(request.GET.get("offset", 0))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid offset")

    parent = get_object_or_404(Comment, pk=parent_id)
    children_qs = parent.children.select_related("author").order_by("path")
    total = children_qs.count()
    children = list(children_qs[offset : offset + PAGE_SIZE])
    next_offset = offset + len(children)
    remaining = max(0, total - next_offset)

    html = render_to_string(
        "core/partials/comment_children.html",
        {
            "children": children,
            "parent": parent,
            "next_offset": next_offset,
            "remaining": remaining,
        },
        request=request,
    )
    return HttpResponse(html)


@login_required
@require_http_methods(["GET"])
def comment_new(request):
    """Return a comment form for replying via HTMX."""

    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")
    if request.headers.get("HX-Request") != "true":
        return HttpResponseBadRequest("Invalid request")

    post_id = request.GET.get("post")
    parent_id = request.GET.get("parent")
    if not post_id:
        return HttpResponseBadRequest("Missing post")
    post = get_object_or_404(Post, pk=post_id)
    parent = None
    if parent_id:
        parent = get_object_or_404(Comment, pk=parent_id, post=post)
    form = CommentForm()
    html = render_to_string(
        "core/partials/comment_form.html",
        {"form": form, "post": post, "parent": parent},
        request=request,
    )
    return HttpResponse(html)


@login_required
@require_POST
def comment_create(request):
    """Create a new comment via HTMX."""

    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")

    if is_new_user(request.user):
        if limit_or_429(request, "comment_new_user", "3/m"):
            return render(request, "429.html", status=429)
    else:
        if limit_or_429(request, "comment_established", "10/m"):
            return render(request, "429.html", status=429)

    post_id = request.POST.get("post")
    if not post_id:
        return HttpResponseBadRequest("Missing post")
    post = get_object_or_404(Post, pk=post_id)

    form = CommentForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest("Invalid comment")

    parent_id = request.POST.get("parent")
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
    post.refresh_from_db(fields=["comment_count"])

    if request.headers.get("HX-Request") == "true":
        item_html = render_to_string(
            "core/partials/comment_item.html", {"comment": comment}, request=request
        )
        plural = "s" if post.comment_count != 1 else ""
        count_html = (
            f'<a href="#comments" id="comment-count" hx-swap-oob="outerHTML">'
            f"{post.comment_count} comment{plural}</a>"
        )
        return HttpResponse(item_html + count_html)

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


@login_required
@require_http_methods(["GET", "POST"])
def comment_edit(request, pk):
    """Edit an existing comment within a 15-minute window."""

    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")

    comment = get_object_or_404(Comment, pk=pk)
    if request.user != comment.author:
        return HttpResponseForbidden("Forbidden")

    if timezone.now() - comment.created_at > timedelta(minutes=15):
        return HttpResponseForbidden("Edit window expired")

    if request.method == "GET":
        form = CommentForm(instance=comment)
        html = render_to_string(
            "core/partials/comment_form.html",
            {"form": form, "comment": comment, "post": comment.post},
            request=request,
        )
        return HttpResponse(html)

    form = CommentForm(request.POST, instance=comment)
    if not form.is_valid():
        return HttpResponseBadRequest("Invalid comment")

    comment.body = form.cleaned_data["body"]
    comment.edited_at = timezone.now()
    comment.save(update_fields=["body", "edited_at"])

    if request.headers.get("HX-Request") == "true":
        html = render_to_string(
            "core/partials/comment_item.html", {"comment": comment}, request=request
        )
        return HttpResponse(html)

    return redirect(
        "post_detail",
        slug=comment.post.community.slug,
        post_id=comment.post.pk,
        post_slug=slugify(comment.post.title),
    )


@login_required
@require_POST
@ratelimit(key="user", rate="10/m", block=False)
def post_delete_owner(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")

    allowed = post.can_author_delete(request.user, minutes=15)
    if not allowed:
        return HttpResponseForbidden("Delete window expired or not author.")
    if getattr(request, "limited", False):
        return HttpResponse("Too many requests", status=429)

    has_comments = Comment.objects.filter(post=post).exists()
    if has_comments:
        post_slug = slugify(post.title)
        post.soft_delete(request.user)
        # HTMX: swap the row to a deleted stub in feeds
        if request.headers.get("HX-Request") == "true":
            html = render_to_string("core/partials/post_deleted_stub.html", {"post": post})
            return HttpResponse(html)
        return redirect(
            "post_detail",
            slug=post.community.slug,
            post_id=post.id,
            post_slug=post_slug,
        )
    else:
        community_slug = post.community.slug
        post.delete()
        if request.headers.get("HX-Request") == "true":
            return HttpResponse("")  # hx-swap="outerHTML" removes the row
        return redirect("community", slug=community_slug)


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
def post_delete_owner(request, pk):
    """Delete a post if the requester is the author or staff."""
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")

    post = get_object_or_404(Post, pk=pk)
    if request.user != post.author and not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")

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
        _, _, new_value = apply_vote(request.user, "comment", pk, value)
    except ValueError:
        return HttpResponseBadRequest("Invalid vote")

    comment = Comment.objects.get(pk=pk)
    score = comment.score
    up_pressed = "true" if new_value == 1 else "false"
    down_pressed = "true" if new_value == -1 else "false"
    url = reverse("vote_comment", args=[pk])
    html = (
        f"<span id='comment-score-{pk}' class='score' hx-swap-oob='outerHTML'>{score}</span>"
        f"<button id='comment-up-{pk}' hx-post='{url}?v=1' hx-swap='none' "
        f"hx-disabled-elt='#comment-up-{pk}, #comment-down-{pk}' "
        f"class='up' aria-label='Upvote' aria-pressed='{up_pressed}' hx-swap-oob='outerHTML'>▲</button>"
        f"<button id='comment-down-{pk}' hx-post='{url}?v=-1' hx-swap='none' "
        f"hx-disabled-elt='#comment-up-{pk}, #comment-down-{pk}' "
        f"class='down' aria-label='Downvote' aria-pressed='{down_pressed}' hx-swap-oob='outerHTML'>▼</button>"
    )
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
