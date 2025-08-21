# config/urls.py

from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Fly.io health check (lightweight, no DB)
    path("healthz", lambda request: HttpResponse("ok", content_type="text/plain"), name="healthz"),
]
