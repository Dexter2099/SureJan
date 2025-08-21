# config/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Lightweight health check for Fly (used by http_service.checks)
    path("healthz", lambda request: HttpResponse("ok"), name="healthz"),

    # App routes
    path("", include("core.urls")),  # expects a core/urls.py with your views
]

# Serve user-uploaded media & collected static only in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
