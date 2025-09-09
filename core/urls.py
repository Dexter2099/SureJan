# core/urls.py
from django.urls import path
from core.views import posts as post_views
from core.views import users as user_views
from core.views import moderation as mod_views
from core.views import reports as report_views

urlpatterns = [
    # Home / front page
    path("", post_views.home, name="home"),
    path("p/<int:pk>", post_views.post_detail_id, name="post_detail_id"),
    path("feed", post_views.feed_list, name="feed_list"),
    path("mission", post_views.mission, name="mission"),
    path("anti-astroturf", post_views.anti_astroturf, name="anti_astroturf"),
    path("mod/astro", mod_views.mod_astro, name="mod_astro"),
    path("methods", mod_views.transparency_methods, name="transparency_methods"),
    path("posts", mod_views.transparency_posts, name="transparency_posts"),
    # Markdown preview endpoint
    path("preview", post_views.preview_markdown, name="preview_markdown"),
    path("markdown/preview/", post_views.markdown_preview, name="markdown_preview"),
    path("submit", post_views.post_submit, name="post_submit"),

    # Post signals
    path("posts/<int:pk>/signals.json", post_views.post_signals_json, name="post_signals_json"),

    # Recovery codes
    path("accounts/recovery-codes/", user_views.recovery_codes, name="recovery_codes"),
    path(
        "accounts/recovery-codes/download/",
        user_views.download_recovery_codes,
        name="download_recovery_codes",
    ),
    path(
        "accounts/security/recovery-codes/regenerate/",
        user_views.regenerate_recovery_codes,
        name="recovery_codes_regenerate",
    ),

    # Post detail (nested under community, with id + slug)
    path(
        "r/<slug:community>/comments/<int:pk>/<slug:slug>",
        post_views.post_detail,
        name="post_detail",
    ),

    # Comments & voting
    # Post moderation
    path("post/<int:pk>/edit/", post_views.post_edit, name="post_edit"),
    path(
        "post/<int:pk>/delete-owner/",
        post_views.post_delete_owner,
        name="post_delete_owner",
    ),
    # Hard delete (admin-only; not linked from templates)
    path("post/<int:pk>/delete/", mod_views.post_delete, name="post_delete"),
    path("post/<int:pk>/remove/", mod_views.post_remove, name="post_remove"),
    path("post/<int:pk>/lock/", mod_views.post_lock, name="post_lock"),
    path("post/<int:pk>/slowmode/", mod_views.post_slowmode, name="post_slowmode"),
    path(
        "post/<int:pk>/domain-throttle/",
        mod_views.post_domain_throttle,
        name="post_domain_throttle",
    ),
    path("report/", report_views.report, name="report"),
    path("reports/", report_views.report_list, name="report_list"),

    # User pages
    path("u/<str:username>/", user_views.user_overview, name="user_overview"),
    path("u/<str:username>/comments/", user_views.user_comments, name="user_comments"),
    path("u/<str:username>/submitted/", user_views.user_submitted, name="user_submitted"),
    path("u/<str:username>/ban/", user_views.ban_user, name="ban_user"),
    path("u/<str:username>/unban/", user_views.unban_user, name="unban_user"),
]
