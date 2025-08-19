"""Core application views."""

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django_ratelimit.decorators import ratelimit, is_ratelimited
from django.template.loader import render_to_string

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm, CommunityCreateForm
from .models import Comment, Community, Post, apply_vote
from .pagination import PAGE_SIZE, build_cursor, parse_cursor


def _render_posts(request, posts, next_before, show_community=False, sort_query=""):
    html = render_to_string(
        "core/partials/post_list.html",
        {"posts": posts, "show_community": show_community},
        request=request,
    )
    if next_before:
        next_url = f"{request.path}?before={next_before}{sort_query}"
        html += render_to_string(
            "core/partials/load_more.html", {"next_url": next_url}, request=request
        )
    return HttpResponse(html)


def home(request):
    """Display the latest posts across all communities."""

    sort = request.GET.get("sort")
    qs = Post.objects.select_related("community", "author")
    qs = parse_cursor(qs, request.GET.get("before"))
    qs = qs.order_by("-created_at", "-id")
    posts = list(qs[: PAGE_SIZE + 1 ])
    next_before = None
    if len(posts) > PAGE_SIZE:
        next_before = build_cursor(posts[PAGE_SIZE - 1])
        posts = posts[:PAGE_SIZE]
    if sort == "hot":
        posts.sort(key=lambda p: (-p.hot_rank, -p.created_at.timestamp(), -p.id))
        sort_query = "&sort=hot"
    else:
        sort_query = ""
    context = {
        "posts": posts,
        "next_before": next_before,
        "sort_query": sort_query,
    }
    if request.headers.get("HX-Request") == "true":
        return _render_posts(request, posts, next_before, show_community=True, sort_query=sort_query)
    return render(
        request,
        "core/home.html",
        {**context},
    )


def community(request, slug):
    """Display posts for a specific community."""

    community = get_object_or_404(Community, slug=slug)
    sort = request.GET.get("sort")
    qs = community.posts.select_related("author")
    qs = parse_cursor(qs, request.GET.get("before"))
    qs = qs.order_by("-created_at", "-id")
    posts = list(qs[: PAGE_SIZE + 1 ])
    next_before = None
    if len(posts) > PAGE_SIZE:
        next_before = build_cursor(posts[PAGE_SIZE - 1])
        posts = posts[:PAGE_SIZE]
    if sort == "hot":
        posts.sort(key=lambda p: (-p.hot_rank, -p.created_at.timestamp(), -p.id))
        sort_query = "&sort=hot"
    else:
        sort_query = ""
    context = {
        "community": community,
        "posts": posts,
        "next_before": next_before,
        "sort_query": sort_query,
    }
    if request.headers.get("HX-Request") == "true":
        return _render_posts(request, posts, next_before, sort_query=sort_query)
    return render(request, "core/community.html", context)


@login_required
def submit_post(request, slug):
    """Submit a new post to a community."""

    community = get_object_or_404(Community, slug=slug)

    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.community = community
            post.author = request.user
            post.save()
            return redirect("community", slug=community.slug)
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


@login_required
@require_http_methods(["GET", "POST"])
@ratelimit(key="user", rate="5/m", method=["POST"], block=False)
def create_community(request):
    if not request.user.is_staff:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
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
