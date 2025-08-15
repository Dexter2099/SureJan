"""Core application views."""

from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.db.models import F

from .forms import PostForm, CommentForm
from .models import Community, Media, Post, Comment, Vote

from io import BytesIO
import uuid
from PIL import Image


def home(request):
    """Display the latest posts across all communities."""

    posts = (
        Post.objects.select_related("community", "author")
        .order_by("-score", "-created_at")[:100]
    )
    return render(request, "core/home.html", {"posts": posts})


def community(request, name):
    """Display posts for a specific community."""

    community = get_object_or_404(Community, name=name)
    posts = (
        Post.objects.filter(community=community)
        .select_related("community", "author")
        .order_by("-score", "-created_at")[:100]
    )
    context = {"community": community, "posts": posts}
    return render(request, "core/community.html", context)


def submit_post(request, name):
    """Submit a new post to a community."""

    community = get_object_or_404(Community, name=name)

    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.community = community
            post.author = request.user

            uploaded = request.FILES.get("file")
            if uploaded:
                image = Image.open(uploaded)
                image = image.convert("RGB")
                image.thumbnail((2560, 2560))

                buffer = BytesIO()
                image.save(buffer, format="WEBP", quality=82)
                buffer.seek(0)

                media = Media(kind="image")
                base = uuid.uuid4().hex
                media.file.save(f"{base}.webp", ContentFile(buffer.read()), save=False)

                width, height = image.size
                thumb_img = image.copy()
                if thumb_img.width > 256:
                    thumb_height = int(thumb_img.height * 256 / thumb_img.width)
                    thumb_img = thumb_img.resize((256, thumb_height))
                buffer_thumb = BytesIO()
                thumb_img.save(buffer_thumb, format="WEBP", quality=82)
                buffer_thumb.seek(0)
                media.thumb.save(f"{base}_thumb.webp", ContentFile(buffer_thumb.read()), save=False)
                media.width = width
                media.height = height
                media.save()
                post.media = media

            post.save()
            return redirect("post_detail", pk=post.pk)
    else:
        form = PostForm()

    context = {"form": form, "community": community}
    return render(request, "core/submit_post.html", context)


def post_detail(request, pk):
    """Display a single post and its comments."""

    post = get_object_or_404(
        Post.objects.select_related("community", "author"), pk=pk
    )
    comments = (
        Comment.objects.filter(post=post)
        .select_related("author")
        .order_by("created_at")
    )
    form = CommentForm()
    context = {"post": post, "comments": comments, "form": form}
    return render(request, "core/post_detail.html", context)


def add_comment(request, pk):
    """Add a comment to a post."""

    post = get_object_or_404(Post, pk=pk)
    if request.method != "POST":
        return redirect("post_detail", pk=post.pk)

    form = CommentForm(request.POST)
    if form.is_valid():
        parent_id = request.POST.get("parent")
        parent = None
        if parent_id:
            parent = Comment.objects.filter(pk=parent_id, post=post).first()
        Comment.objects.create(
            post=post,
            author=request.user,
            body=form.cleaned_data["body"],
            parent=parent,
        )
    return redirect("post_detail", pk=post.pk)


@login_required
@require_POST
def vote_post(request, pk):
    """Handle voting on a post."""

    try:
        value = int(request.POST.get("v"))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid vote")
    if value not in (-1, 1):
        return HttpResponseBadRequest("Invalid vote")

    post = get_object_or_404(Post, pk=pk)
    vote, created = Vote.objects.get_or_create(
        user=request.user,
        target_type="post",
        target_id=pk,
        defaults={"value": value},
    )
    if created:
        Post.objects.filter(pk=pk).update(score=F("score") + value)
    elif vote.value != value:
        diff = value - vote.value
        vote.value = value
        vote.save(update_fields=["value"])
        Post.objects.filter(pk=pk).update(score=F("score") + diff)
    post.refresh_from_db(fields=["score"])
    return HttpResponse(f"<span id='post-score-{pk}'>{post.score}</span>")


@login_required
@require_POST
def vote_comment(request, pk):
    """Handle voting on a comment."""

    try:
        value = int(request.POST.get("v"))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid vote")
    if value not in (-1, 1):
        return HttpResponseBadRequest("Invalid vote")

    comment = get_object_or_404(Comment, pk=pk)
    vote, created = Vote.objects.get_or_create(
        user=request.user,
        target_type="comment",
        target_id=pk,
        defaults={"value": value},
    )
    if created:
        Comment.objects.filter(pk=pk).update(score=F("score") + value)
    elif vote.value != value:
        diff = value - vote.value
        vote.value = value
        vote.save(update_fields=["value"])
        Comment.objects.filter(pk=pk).update(score=F("score") + diff)
    comment.refresh_from_db(fields=["score"])
    return HttpResponse(f"<span id='comment-score-{pk}'>{comment.score}</span>")

