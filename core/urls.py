# core/urls.py
from django.urls import path
from . import views as core_views

urlpatterns = [
    # Home / front page
    path("", core_views.home, name="home"),
    path("mission/", core_views.mission, name="mission"),

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
    path("r/<slug:slug>/", core_views.community, name="community"),
    path("r/<slug:slug>/submit/", core_views.submit_post, name="submit_post"),
    path("r/<slug:slug>/wiki/", core_views.community_wiki, name="community_wiki"),

    # Post detail (nested under community, with id + slug)
    path(
        "r/<slug:slug>/comments/<int:post_id>/<slug:post_slug>/",
        core_views.post_detail,
        name="post_detail",
    ),

    # Comments & voting
    path("comment/<int:post_id>/reply/", core_views.comment_reply, name="comment_reply"),
    path("comment/<int:post_id>/reply-form/", core_views.comment_reply_form, name="comment_reply_form"),
    path("comment/<int:pk>/delete/", core_views.comment_delete, name="comment_delete"),
    path("vote/post/<int:pk>/", core_views.vote_post, name="vote_post"),
    path("vote/comment/<int:pk>/", core_views.vote_comment, name="vote_comment"),
    path("post/<int:pk>/delete/", core_views.post_delete, name="post_delete"),
    path("report/<str:target_type>/<int:pk>/", core_views.report, name="report"),

    # User pages
    path("u/<str:username>/", core_views.user_overview, name="user_overview"),
    path("u/<str:username>/comments/", core_views.user_comments, name="user_comments"),
    path("u/<str:username>/submitted/", core_views.user_submitted, name="user_submitted"),
]
