# config/urls.py
from django.conf import settings
from django.conf.urls.static import static as serve_static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.templatetags.static import static

urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url=static("favicon.ico"), permanent=True)),

    # Admin
    path("admin/", admin.site.urls),

    # Lightweight health check for Fly (used by http_service.checks)
    path("healthz", lambda request: HttpResponse("ok"), name="healthz"),

    # App routes
    path("", include("core.urls")),  # expects a core/urls.py with your views
]

# Serve user-uploaded media & collected static only in development
if settings.DEBUG:
    urlpatterns += serve_static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += serve_static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
