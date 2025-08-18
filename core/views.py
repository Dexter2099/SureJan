"""Core application views."""

from django.contrib.auth.decorators import login_required
from django_ratelimit.decorators import ratelimit

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm
from .models import Comment, Community, Post, apply_vote


def home(request):
    """Display the latest posts across all communities."""

    posts = (
        Post.objects.select_related("community", "author")
        .order_by("-created_at")[:50]
    )
    return render(request, "core/home.html", {"posts": posts})


def community(request, name):
    """Display posts for a specific community."""

    community = get_object_or_404(Community, name=name)
    posts = (
        community.posts.select_related("author")
        .order_by("-created_at")[:50]
    )
    context = {"community": community, "posts": posts}
    return render(request, "core/community.html", context)

@login_required
def submit_post(request, name):
    """Submit a new post to a community."""

    community = get_object_or_404(Community, name=name)

    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.community = community
            post.author = request.user
            post.save()
            return redirect("community", name=community.name)
    else:
        form = PostForm()

    context = {"form": form, "community": community}
    return render(request, "core/submit_post.html", context)


def post_detail(request, pk):
    """Display a single post and its comments."""

    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.select_related("author").order_by("created_at")
    form = CommentForm()
    context = {"post": post, "comments": comments, "form": form}
    return render(request, "core/post_detail.html", context)


@login_required
@require_POST
def add_comment(request, pk):
    """Add a comment to a post."""

    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        Comment.objects.create(
            post=post, author=request.user, body=form.cleaned_data["body"]
        )
    return redirect("post_detail", pk=post.pk)


@login_required
@require_POST
@ratelimit(key="user_or_ip", rate="20/m", block=True)
def vote_post(request, pk):
    """Handle voting on a post."""

    try:
        value = int(request.POST.get("v"))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid vote")

    try:
        new_score = apply_vote(request.user, "post", pk, value)
    except ValueError:
        return HttpResponseBadRequest("Invalid vote")

    return HttpResponse(f"<span id='post-score-{pk}'>{new_score}</span>")


@login_required
@require_POST
@ratelimit(key="user_or_ip", rate="20/m", block=True)
def vote_comment(request, pk):
    """Handle voting on a comment."""

    try:
        value = int(request.POST.get("v"))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid vote")

    try:
        new_score = apply_vote(request.user, "comment", pk, value)
    except ValueError:
        return HttpResponseBadRequest("Invalid vote")

    return HttpResponse(f"<span id='comment-score-{pk}'>{new_score}</span>")
