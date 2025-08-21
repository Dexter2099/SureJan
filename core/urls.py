# core/urls.py — GMFU (Good, Minimal, Fast, Understandable)
#
# This file is resilient: it will use your real views if they exist,
# otherwise it falls back to simple template views (or a tiny HttpResponse)
# so the app always boots on Fly while you wire things up.

from django.http import HttpResponse
from django.urls import path
from django.views.generic import TemplateView

try:
    from . import views as _views  # your real views (if present)
except Exception:  # import-safe in case views.py has errors during boot
    _views = None


def _resolve_view(candidates, *, template=None, text="OK"):
    """
    Return the first callable view found in `candidates` from core.views.
    If none exist, return a TemplateView (if `template` given),
    otherwise return a minimal HttpResponse fallback.
    """
    for name in candidates:
        v = getattr(_views, name, None) if _views else None
        if callable(v):
            return v
    if template:
        return TemplateView.as_view(template_name=template)
    return lambda request, **kw: HttpResponse(text)


# --- Resilient route bindings -----------------------------------------------

home_view = _resolve_view(
    ["home", "index", "feed", "frontpage"], template="home.html", text="Home"
)

community_view = _resolve_view(
    ["community", "community_feed", "subreddit"], template="community.html", text="Community"
)

post_detail_view = _resolve_view(
    ["post_detail", "comments", "thread"], template="post_detail.html", text="Post"
)

user_profile_view = _resolve_view(
    ["user_profile", "profile"], template="user_profile.html", text="User profile"
)

submit_post_view = _resolve_view(
    ["submit_post", "create_post", "submit"], template="submit.html", text="Submit post"
)

wiki_view = _resolve_view(
    ["wiki", "community_wiki"], template="wiki.html", text="Wiki"
)

urlpatterns = [
    # Front page / feed
    path("", home_view, name="home"),

    # Community feed: /r/<slug>/
    path("r/<slug:slug>/", community_view, name="community"),

    # Post detail + comments: /r/<slug>/comments/<post_id>/
    path("r/<slug:slug>/comments/<int:post_id>/", post_detail_view, name="post_detail"),

    # User profile: /u/<username>/
    path("u/<str:username>/", user_profile_view, name="user_profile"),

    # Submit a post: /submit/
    path("submit/", submit_post_view, name="submit_post"),

    # Community wiki (optional)
    path("wiki/", wiki_view, name="wiki"),
]

# Optional: add lightweight “alive” endpoint for quick manual checks
# urlpatterns += [path("alive", lambda r: HttpResponse("ok"), name="alive")]
