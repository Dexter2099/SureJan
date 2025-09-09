from django.contrib import messages
from django.core.paginator import EmptyPage, Paginator
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET
from django_ratelimit.core import is_ratelimited

from .forms import CommunityCreateForm
from .models import Community
from core.pagination import PAGE_SIZE
from core.services import TAB_ORDER, feed_queryset
from core.utils.view_helpers import SORT_TABS, _is_banned


@require_GET
def communities_index(request):
    """List available communities."""
    sort = request.GET.get("sort", "hot")
    if sort not in TAB_ORDER:
        sort = "hot"

    t = request.GET.get("t")
    allowed = {"24h", "7d", "all"}
    if sort != "top" or t not in allowed:
        t = None
    if sort == "top" and t is None:
        t = "all"

    communities = [
        {"slug": "news", "name": "News"},
        {"slug": "brisbane", "name": "Brisbane"},
        {"slug": "history", "name": "History"},
        {"slug": "politics", "name": "Politics"},
        {"slug": "social", "name": "Social"},
    ]

    qs = ""
    if sort != "hot":
        qs = f"?sort={sort}"
        if sort == "top" and t and t != "all":
            qs += f"&t={t}"

    ctx = {"communities": communities, "qs": qs, "sort": sort, "t": t}
    return render(request, "communities/index.html", ctx)


def community(request, slug):
    """Display posts for a specific community."""
    try:
        community = Community.objects.get(slug=slug)
    except Community.DoesNotExist:
        return redirect("/")
    sort = request.GET.get("sort", "hot")
    if sort not in TAB_ORDER:
        sort = "hot"

    t = request.GET.get("t")
    allowed = {"24h", "7d", "all"}
    if sort != "top" or t not in allowed:
        t = None
    if sort == "top" and t is None:
        t = "all"

    page_param = request.GET.get("page", "1")
    try:
        requested = int(page_param)
    except (TypeError, ValueError):
        messages.error(request, "Invalid page number.")
        return redirect(request.path)
    if requested < 1:
        messages.error(request, "Invalid page number.")
        return redirect(request.path)

    base_qs = community.posts.filter(is_deleted=False).select_related("author")
    qs = feed_queryset(sort, t, base_qs=base_qs)

    paginator = Paginator(qs, PAGE_SIZE)
    page = max(1, min(requested, paginator.num_pages))
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    posts = list(page_obj.object_list)
    next_page = page_obj.next_page_number() if page_obj.has_next() else None

    sort_query = ""
    if sort and sort != "hot":
        sort_query += f"&sort={sort}"
    if sort == "top" and t:
        sort_query += f"&t={t}"

    if request.headers.get("HX-Request") == "true":
        from core.utils.view_helpers import _render_posts

        return _render_posts(request, posts, next_page, sort_query=sort_query)

    context = {
        "community": community,
        "community_slug": community.slug,
        "posts": posts,
        "next_page": next_page,
        "sort_query": sort_query,
        "sort": sort,
        "t": t,
        "sort_tabs": SORT_TABS,
    }
    return render(request, "communities/community.html", context)


def community_wiki(request, slug):
    """Render the community wiki if available, otherwise show a stub."""
    community = get_object_or_404(Community, slug=slug)
    context = {"community": community}
    return render(request, "communities/wiki.html", context)


def create_community(request):
    if not request.user.is_staff:
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")
    if request.method == "POST":
        if is_ratelimited(
            request,
            group="community-create",
            key="user",
            rate="5/m",
            method=["POST"],
            increment=True,
        ):
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

