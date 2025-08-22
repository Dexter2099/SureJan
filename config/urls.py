from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.templatetags.static import static
from django.conf import settings
from django.conf.urls.static import static as static_serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", lambda request: HttpResponse("ok"), name="healthz"),

    # Redirect bare /favicon.ico → collected static file
    path("favicon.ico", RedirectView.as_view(
        url=static("favicon.ico"), permanent=False
    )),

    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static_serve(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static_serve(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

