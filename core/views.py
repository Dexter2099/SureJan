"""Core application views."""

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_protect
from django_ratelimit.decorators import ratelimit, is_ratelimited
from django.template.loader import render_to_string

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.db.models import F

from .forms import CommentForm, PostForm, CommunityCreateForm
from .models import Comment, Community, Post
from .votes import apply_vote
from .pagination import PAGE_SIZE


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

    tab = request.GET.get("t", "best")
    order = FEED_ORDER.get(tab, FEED_ORDER["best"])
    page = int(request.GET.get("page", "1") or 1)

    qs = Post.objects.select_related("community", "author").order_by(*order)

    offset = (page - 1) * PAGE_SIZE
    posts = list(qs[offset : offset + PAGE_SIZE + 1])
    next_page = page + 1 if len(posts) > PAGE_SIZE else None
    posts = posts[:PAGE_SIZE]

    sort_query = f"&t={tab}" if tab and tab != "best" else ""
    context = {
        "posts": posts,
        "next_page": next_page,
        "sort_query": sort_query,
        "tab": tab,
    }
    if request.headers.get("HX-Request") == "true":
        return _render_posts(
            request, posts, next_page, show_community=True, sort_query=sort_query
        )
    return render(request, "core/home.html", context)


def community(request, slug):
    """Display posts for a specific community."""

    community = get_object_or_404(Community, slug=slug)
    tab = request.GET.get("t", "best")
    order = FEED_ORDER.get(tab, FEED_ORDER["best"])
    page = int(request.GET.get("page", "1") or 1)

    qs = community.posts.select_related("author").order_by(*order)
    offset = (page - 1) * PAGE_SIZE
    posts = list(qs[offset : offset + PAGE_SIZE + 1])
    next_page = page + 1 if len(posts) > PAGE_SIZE else None
    posts = posts[:PAGE_SIZE]

    sort_query = f"&t={tab}" if tab and tab != "best" else ""
    context = {
        "community": community,
        "posts": posts,
        "next_page": next_page,
        "sort_query": sort_query,
        "tab": tab,
    }
    if request.headers.get("HX-Request") == "true":
        return _render_posts(request, posts, next_page, sort_query=sort_query)
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
    """Reply to a post or comment."""

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
@require_POST
@csrf_protect
@ratelimit(key="user_or_ip", rate="20/m", block=True)
def vote_post(request, pk):
    """Handle voting on a post."""

    try:
        value = int(request.GET.get("v"))
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
@ratelimit(key="user_or_ip", rate="20/m", block=True)
def vote_comment(request, pk):
    """Handle voting on a comment."""

    try:
        value = int(request.GET.get("v"))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid vote")

    try:
        apply_vote(request.user, "comment", pk, value)
    except ValueError:
        return HttpResponseBadRequest("Invalid vote")

    score = Comment.objects.get(pk=pk).score
    return HttpResponse(f"<span id='comment-score-{pk}'>{score}</span>")


def community_wiki(request, slug):
    """Placeholder view for community wiki."""

    return HttpResponse("wiki")


def user_overview(request, username):
    """User overview page stub."""

    return HttpResponse(f"Profile for {username}")


def user_comments(request, username):
    """User comments page stub."""

    return HttpResponse(f"Comments by {username}")


def user_submitted(request, username):
    """User submitted posts page stub."""

    return HttpResponse(f"Submissions by {username}")


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
