# core/urls.py
from django.urls import path
from core.views import users as user_views
from core.views import reports as report_views

urlpatterns = [
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

    # Reports
    path("report/", report_views.report, name="report"),
    path("reports/", report_views.report_list, name="report_list"),

    # User pages
    path("u/<str:username>/", user_views.user_overview, name="user_overview"),
    path("u/<str:username>/comments/", user_views.user_comments, name="user_comments"),
    path("u/<str:username>/submitted/", user_views.user_submitted, name="user_submitted"),
    path("u/<str:username>/ban/", user_views.ban_user, name="ban_user"),
    path("u/<str:username>/unban/", user_views.unban_user, name="unban_user"),
]
