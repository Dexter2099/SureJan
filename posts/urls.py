from django.urls import path
from core.views import posts as post_views
from core.views import moderation as mod_views

urlpatterns = [
    path("", post_views.home, name="home"),
    path("p/<int:pk>", post_views.post_detail_id, name="post_detail_id"),
    path("feed", post_views.feed_list, name="feed_list"),
    path("mission", post_views.mission, name="mission"),
    path("anti-astroturf", post_views.anti_astroturf, name="anti_astroturf"),
    path("mod/astro", mod_views.mod_astro, name="mod_astro"),
    path("methods", mod_views.transparency_methods, name="transparency_methods"),
    path("posts", mod_views.transparency_posts, name="transparency_posts"),
    path("preview", post_views.preview_markdown, name="preview_markdown"),
    path("markdown/preview/", post_views.markdown_preview, name="markdown_preview"),
    path("submit", post_views.post_submit, name="post_submit"),
    path("posts/<int:pk>/signals.json", post_views.post_signals_json, name="post_signals_json"),
    path(
        "r/<slug:community>/comments/<int:pk>/<slug:slug>",
        post_views.post_detail,
        name="post_detail",
    ),
    path("post/<int:pk>/edit/", post_views.post_edit, name="post_edit"),
    path("post/<int:pk>/delete-owner/", post_views.post_delete_owner, name="post_delete_owner"),
    path("post/<int:pk>/delete/", mod_views.post_delete, name="post_delete"),
    path("post/<int:pk>/remove/", mod_views.post_remove, name="post_remove"),
    path("post/<int:pk>/lock/", mod_views.post_lock, name="post_lock"),
    path("post/<int:pk>/slowmode/", mod_views.post_slowmode, name="post_slowmode"),
    path(
        "post/<int:pk>/domain-throttle/",
        mod_views.post_domain_throttle,
        name="post_domain_throttle",
    ),
]
