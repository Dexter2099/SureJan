"""Core application views."""

from django.shortcuts import get_object_or_404, render

from .models import Community, Post


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

