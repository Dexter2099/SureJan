import logging
from types import SimpleNamespace
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import DataError, IntegrityError

from core.utils.view_helpers import (
    _find_offending_field,
    _is_banned,
    is_new_user,
    limit_or_429,
)
from core.pagination import PAGE_SIZE
from core.models import Post
from core.http import login_required_htmx

from .models import Comment
from .forms import CommentForm
from .services import create_comment, edit_comment, delete_comment

logger = logging.getLogger(__name__)


@login_required
@require_POST
@csrf_protect
def comment_reply(request, post_id):
    """Create a new comment on a post or comment."""
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")
    post = get_object_or_404(Post.objects.filter(is_deleted=False), pk=post_id)
    if post.is_locked:
        return HttpResponseForbidden("Comments locked")
    if post.slowmode:
        rate = f"1/{post.slowmode}s"
        if limit_or_429(request, f"slow_{post.pk}", rate):
            return render(request, "429.html", status=429)
    if getattr(post, "astro_score", None) and post.astro_score.score >= settings.ASTRO_SLOWMODE_THRESHOLD:
        if limit_or_429(request, f"astro_slow_{post.pk}", settings.ASTRO_SLOWMODE_RATE):
            return render(request, "429.html", status=429)

    if is_new_user(request.user):
        if limit_or_429(request, "comment_new_user", "3/m"):
            return render(request, "429.html", status=429)
    else:
        if limit_or_429(request, "comment_established", "10/m"):
            return render(request, "429.html", status=429)

    form = CommentForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest("Invalid comment")

    parent_id = request.POST.get("parent_id")
    parent = None
    if parent_id:
        parent = get_object_or_404(Comment, pk=parent_id, post=post)

    try:
        comment = create_comment(
            post=post,
            author=request.user,
            body=form.cleaned_data["body"],
            parent=parent,
        )
    except (DataError, IntegrityError):
        field, size = _find_offending_field(form)
        logger.error("path=%s field=%s size=%s", request.path, field, size)
        form.add_error(
            None, "One or more fields exceed the allowed length."
        )
        class Dummy(SimpleNamespace):
            def __bool__(self):
                return False
        dummy = Dummy(pk=None)
        return render(
            request,
            "comments/comment_form.html",
            {"form": form, "post": post, "parent": parent or dummy, "comment": dummy},
            status=400,
        )

    if request.headers.get("HX-Request") == "true":
        depth = comment.path.count("/")
        return render(
            request,
            "comments/comment_row.html",
            {"comment": comment, "depth": depth},
        )

    return redirect(
        "post_detail",
        community=post.community.slug,
        pk=post.pk,
        slug=post.slug,
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
        "comments/comment_children.html",
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
    post = get_object_or_404(Post.objects.filter(is_deleted=False), pk=post_id)
    if post.is_locked:
        return HttpResponseForbidden("Comments locked")
    parent = None
    if parent_id:
        parent = get_object_or_404(Comment, pk=parent_id, post=post)
    form = CommentForm()
    html = render_to_string(
        "comments/comment_form.html",
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
    post_id = request.POST.get("post")
    if not post_id:
        return HttpResponseBadRequest("Missing post")
    post = get_object_or_404(Post.objects.filter(is_deleted=False), pk=post_id)
    if post.is_locked:
        return HttpResponseForbidden("Comments locked")
    if post.slowmode:
        rate = f"1/{post.slowmode}s"
        if limit_or_429(request, f"slow_{post.pk}", rate):
            return render(request, "429.html", status=429)
    if getattr(post, "astro_score", None) and post.astro_score.score >= settings.ASTRO_SLOWMODE_THRESHOLD:
        if limit_or_429(request, f"astro_slow_{post.pk}", settings.ASTRO_SLOWMODE_RATE):
            return render(request, "429.html", status=429)
    if is_new_user(request.user):
        if limit_or_429(request, "comment_new_user", "3/m"):
            return render(request, "429.html", status=429)
    else:
        if limit_or_429(request, "comment_established", "10/m"):
            return render(request, "429.html", status=429)

    form = CommentForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest("Invalid comment")

    parent_id = request.POST.get("parent")
    parent = None
    if parent_id:
        parent = get_object_or_404(Comment, pk=parent_id, post=post)

    try:
        comment = create_comment(
            post=post,
            author=request.user,
            body=form.cleaned_data["body"],
            parent=parent,
        )
        post.refresh_from_db(fields=["comment_count"])
    except (DataError, IntegrityError):
        field, size = _find_offending_field(form)
        logger.error("path=%s field=%s size=%s", request.path, field, size)
        form.add_error(
            None, "One or more fields exceed the allowed length."
        )
        class Dummy(SimpleNamespace):
            def __bool__(self):
                return False
        dummy = Dummy(pk=None)
        return render(
            request,
            "comments/comment_form.html",
            {"form": form, "post": post, "parent": parent or dummy, "comment": dummy},
            status=400,
        )

    if request.headers.get("HX-Request") == "true":
        item_html = render_to_string(
            "comments/comment_item.html", {"comment": comment}, request=request
        )
        plural = "s" if post.comment_count != 1 else ""
        count_html = (
            f'<a href="#comments" id="comment-count" hx-swap-oob="outerHTML">'
            f"{post.comment_count} comment{plural}</a>"
        )
        return HttpResponse(item_html + count_html)

    return redirect(
        "post_detail",
        community=post.community.slug,
        pk=post.pk,
        slug=post.slug,
    )


@require_GET
def comment_reply_form(request, pk):
    parent = get_object_or_404(Comment, pk=pk)
    return render(
        request,
        "comments/reply_form.html",
        {"parent_id": parent.pk, "post": parent.post},
    )


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
            "comments/comment_form.html",
            {
                "form": form,
                "comment": comment,
                "post": comment.post,
                "parent": comment,
            },
            request=request,
        )
        return HttpResponse(html)

    form = CommentForm(request.POST, instance=comment)
    if not form.is_valid():
        return HttpResponseBadRequest("Invalid comment")

    edit_comment(comment, form.cleaned_data["body"])

    if request.headers.get("HX-Request") == "true":
        html = render_to_string(
            "comments/comment_item.html", {"comment": comment}, request=request
        )
        return HttpResponse(html)

    return redirect(
        "post_detail",
        community=comment.post.community.slug,
        pk=comment.post.pk,
        slug=comment.post.slug,
    )


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

    delete_comment(comment, request.user)

    if request.headers.get("HX-Request") == "true":
        html = render_to_string(
            "comments/comment_deleted_stub.html", {"comment": comment}, request=request
        )
        return HttpResponse(html)

    return redirect(
        "post_detail",
        community=comment.post.community.slug,
        pk=comment.post.pk,
        slug=comment.post.slug,
    )
