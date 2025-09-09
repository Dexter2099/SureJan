"""Post related views."""

import hashlib
import json
import logging

import bleach
import mistune
from django.utils.safestring import mark_safe

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import EmptyPage, Paginator
from django.db import DataError, IntegrityError
from django.db.models import F
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.cache import patch_cache_control
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import (
    require_GET,
    require_POST,
    require_http_methods,
)
from django_ratelimit.decorators import ratelimit

from ..forms import PostForm
from ..models import Post
from comments.models import Comment
from ..pagination import PAGE_SIZE
from ..services.astro import compute_post_signals
from ..services.feed import TAB_ORDER, feed_queryset
from ..http import login_required_htmx
from ..utils.view_helpers import (
    _is_banned,
    _find_offending_field,
    _render_posts,
    is_new_user,
    limit_or_429,
    SORT_TABS,
)


logger = logging.getLogger(__name__)

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
