# config/urls.py
from django.conf import settings
from django.conf.urls.static import static as serve_static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", lambda request: HttpResponse("ok"), name="healthz"),
    path("", include("core.urls")),
]

# Dev-only static/media
if settings.DEBUG:
    urlpatterns += serve_static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += serve_static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

