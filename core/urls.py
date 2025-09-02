# core/urls.py
from django.urls import path
from core import views as core_views

urlpatterns = [
    # Home / front page
    path("", core_views.home, name="home"),
    path("p/<int:pk>", core_views.post_detail_id, name="post_detail_id"),
    path("feed", core_views.feed_list, name="feed_list"),
    path("mission", core_views.mission, name="mission"),
    path("anti-astroturf", core_views.anti_astroturf, name="anti_astroturf"),
    path("mod/astro", core_views.mod_astro, name="mod_astro"),
    path("methods", core_views.transparency_methods, name="transparency_methods"),
    path("posts", core_views.transparency_posts, name="transparency_posts"),
    # Markdown preview endpoint
    path("preview", core_views.preview_markdown, name="preview_markdown"),
    path("oembed/preview", core_views.oembed_preview, name="oembed_preview"),
    path("submit", core_views.post_submit, name="post_submit"),

    # Post signals
    path("posts/<int:pk>/signals.json", core_views.post_signals_json, name="post_signals_json"),
    path("posts/<int:pk>/signals/chips", core_views.post_signals_chips, name="post_signals_chips"),

    # Recovery codes
    path("accounts/recovery-codes/", core_views.recovery_codes, name="recovery_codes"),
    path(
        "accounts/recovery-codes/download/",
        core_views.download_recovery_codes,
        name="download_recovery_codes",
    ),
    path(
        "accounts/security/recovery-codes/regenerate/",
        core_views.regenerate_recovery_codes,
        name="recovery_codes_regenerate",
    ),

    # Create a community
    path("c/new/", core_views.create_community, name="community_create"),

    # Community pages (slug-based, /r/<slug>/…)
    path("r/<slug:slug>/wiki", core_views.community_wiki, name="community_wiki"),

    # Post detail (nested under community, with id + slug)
    path(
        "r/<slug:community>/comments/<int:pk>/<slug:slug>",
        core_views.post_detail,
        name="post_detail",
    ),

    # Comments & voting
    path("comment/<int:post_id>/reply/", core_views.comment_reply, name="comment_reply"),
    path("comment/<int:post_id>/reply-form/", core_views.comment_reply_form, name="comment_reply_form"),
    path("comment/<int:pk>/delete/", core_views.comment_delete, name="comment_delete"),
    path("comment/<int:pk>/edit/", core_views.comment_edit, name="comment_edit"),
    path("comments/new", core_views.comment_new, name="comment_new"),
    path("comments/create", core_views.comment_create, name="comment_create"),
    path("comments/children", core_views.comment_children, name="comment_children"),
    path("vote/post/<int:pk>/", core_views.vote_post, name="vote_post"),
    path("comments/vote/<int:pk>/", core_views.vote_comment, name="vote_comment"),
    # Post moderation
    path("post/<int:pk>/edit/", core_views.post_edit, name="post_edit"),
    path(
        "post/<int:pk>/delete-owner/",
        core_views.post_delete_owner,
        name="post_delete_owner",
    ),
    path("post/<int:pk>/delete/", core_views.post_delete, name="post_delete"),
    path("post/<int:pk>/remove/", core_views.post_remove, name="post_remove"),
    path("post/<int:pk>/lock/", core_views.post_lock, name="post_lock"),
    path("post/<int:pk>/slowmode/", core_views.post_slowmode, name="post_slowmode"),
    path(
        "post/<int:pk>/domain-throttle/",
        core_views.post_domain_throttle,
        name="post_domain_throttle",
    ),
    path("report/", core_views.report, name="report"),
    path("reports/", core_views.report_list, name="report_list"),

    # User pages
    path("u/<str:username>/", core_views.user_overview, name="user_overview"),
    path("u/<str:username>/comments/", core_views.user_comments, name="user_comments"),
    path("u/<str:username>/submitted/", core_views.user_submitted, name="user_submitted"),
    path("u/<str:username>/ban/", core_views.ban_user, name="ban_user"),
    path("u/<str:username>/unban/", core_views.unban_user, name="unban_user"),
]
