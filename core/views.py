"""Core application views."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_protect
from django_ratelimit.decorators import ratelimit, is_ratelimited
from django.template.loader import render_to_string

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.db.models import F
from django import forms

from .forms import CommentForm, PostForm, CommunityCreateForm
from .models import Comment, Community, Post
from .votes import apply_vote
from .pagination import PAGE_SIZE


def healthz(_request):
    """Simple health check endpoint."""
    return HttpResponse("ok", content_type="text/plain")


class SignupForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


def signup(request):
    """Create a new user account and log them in."""

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            U = get_user_model()
            username = form.cleaned_data["username"]
            if U.objects.filter(username=username).exists():
                form.add_error("username", "That username is taken.")
            else:
                user = U.objects.create_user(
                    username=username, password=form.cleaned_data["password"]
                )
                login(request, user)
                return redirect("home")
    else:
        form = SignupForm()
    return render(request, "registration/signup.html", {"form": form})


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
@ratelimit(key="user", rate="30/m", method=["POST"], block=False)
def submit_post(request, slug):
    """Submit a new post to a community."""

    community = get_object_or_404(Community, slug=slug)

    if request.method == "POST":
        if getattr(request, "limited", False):
            resp = HttpResponse("Too many requests", status=429)
            resp.headers["X-RateLimit-Triggered"] = "1"
            return resp
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.community = community
            post.author = request.user
            post.save()
            messages.success(request, "Post submitted")
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
@ratelimit(key="user", rate="30/m", method=["POST"], block=False)
def comment_reply(request, post_id):
    """Create a new comment on a post or comment."""

    if getattr(request, "limited", False):
        if request.headers.get("HX-Request") == "true":
            html = render_to_string(
                "core/partials/ratelimit.html", {"action": "comment"}, request=request
            )
            resp = HttpResponse(html, status=429)
        else:
            resp = HttpResponse("Too many requests", status=429)
        resp.headers["X-RateLimit-Triggered"] = "1"
        return resp

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
@require_POST
@csrf_protect
@ratelimit(key="user", rate="120/m", method=["POST"], block=False)
def vote_post(request, pk):
    """Handle voting on a post."""

    if getattr(request, "limited", False):
        resp = HttpResponse("Too many requests", status=429)
        resp.headers["X-RateLimit-Triggered"] = "1"
        return resp

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
@ratelimit(key="user", rate="120/m", method=["POST"], block=False)
def vote_comment(request, pk):
    """Handle voting on a comment."""

    if getattr(request, "limited", False):
        resp = HttpResponse("Too many requests", status=429)
        resp.headers["X-RateLimit-Triggered"] = "1"
        return resp

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
