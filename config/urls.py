# config/urls.py
from django.conf import settings
from django.conf.urls.static import static as serve_static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from django.views.generic import TemplateView
from django.http import HttpResponse

from core import views as core

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("healthz", lambda request: HttpResponse("ok"), name="healthz"),
    path("accounts/login/", core.RateLimitedLoginView.as_view(), name="login"),
    path(
        "accounts/logout/",
        LogoutView.as_view(next_page="/"),
        name="logout",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/signup/", core.signup, name="signup"),
    path("terms/", TemplateView.as_view(template_name="legal/terms.html"), name="terms"),
    path("privacy/", TemplateView.as_view(template_name="legal/privacy.html"), name="privacy"),
    path("rules/", TemplateView.as_view(template_name="legal/rules.html"), name="rules"),
    path("", include("core.urls")),
]

# Dev-only static/media
if settings.DEBUG:
    urlpatterns += serve_static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += serve_static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

