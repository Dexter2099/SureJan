"""Moderation-related views."""

from datetime import timedelta

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.core.paginator import EmptyPage, Paginator
from django.contrib import messages

from ..models import Post
from ..services.astro import compute_post_signals
from .. import mod


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


@require_POST
@csrf_protect
def post_delete(request, pk):
    """Hard delete a post."""
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
