"""URL configuration for the project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from core import views as core_views
from core.views import healthz


urlpatterns = [
    path("", core_views.home, name="home"),
    path("c/new/", core_views.create_community, name="community_create"),
    path("r/<slug:slug>/", core_views.community, name="community"),
    path("r/<slug:slug>/submit/", core_views.submit_post, name="submit_post"),
    path("r/<slug:slug>/wiki/", core_views.community_wiki, name="community_wiki"),
    path(
        "r/<slug:slug>/comments/<int:post_id>/<slug:post_slug>/",
        core_views.post_detail,
        name="post_detail",
    ),
    path("comment/<int:post_id>/reply/", core_views.comment_reply, name="comment_reply"),
    path("vote/post/<int:pk>/", core_views.vote_post, name="vote_post"),
    path("vote/comment/<int:pk>/", core_views.vote_comment, name="vote_comment"),
    path("u/<str:username>/", core_views.user_overview, name="user_overview"),
    path("u/<str:username>/comments/", core_views.user_comments, name="user_comments"),
    path("u/<str:username>/submitted/", core_views.user_submitted, name="user_submitted"),
    path("admin/", admin.site.urls),
]

urlpatterns += [path("healthz", healthz, name="healthz")]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
