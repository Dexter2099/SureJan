from django.urls import path
from django.views.generic import RedirectView

from . import views


urlpatterns = [
    path("r", views.communities_index, name="communities_index"),
    path("r/<slug:slug>/", views.community, name="community"),
    path("r/<slug:slug>/wiki", views.community_wiki, name="community_wiki"),
    path("c/new/", views.create_community, name="community_create"),
    # Legacy/alternate route: keep /community/<slug>/ working alongside /r/<slug>/
    path(
        "community/<slug:slug>/",
        RedirectView.as_view(pattern_name="community", permanent=True),
    ),
    path(
        "c/<slug:slug>/",
        RedirectView.as_view(pattern_name="community", permanent=True),
    ),
]
