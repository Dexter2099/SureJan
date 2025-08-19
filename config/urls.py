"""URL configuration for the project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from core import views as core_views


urlpatterns = [
    path("", core_views.home, name="home"),
    path("c/new/", core_views.create_community, name="community_create"),
    path("c/<slug:slug>/", core_views.community, name="community"),
    path("c/<slug:slug>/submit/", core_views.submit_post, name="submit_post"),
    path("post/<int:pk>/", core_views.post_detail, name="post_detail"),
    path("post/<int:pk>/comment/", core_views.add_comment, name="add_comment"),
    path("vote/post/<int:pk>/", core_views.vote_post, name="vote_post"),
    path("vote/comment/<int:pk>/", core_views.vote_comment, name="vote_comment"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
