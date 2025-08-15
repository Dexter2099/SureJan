<<<<<<< HEAD
=======
"""URL configuration for the project."""

from django.conf import settings
from django.conf.urls.static import static
>>>>>>> e519127d299e92c16c01fb19bd5dd78662494972
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

from core import views as core_views


urlpatterns = [
    path("admin/", admin.site.urls),
<<<<<<< HEAD
    path("", views.home, name="home"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
=======
    path("", core_views.home, name="home"),
    path("post/<int:pk>/", core_views.post_detail, name="post_detail"),
    path("post/<int:pk>/comment/", core_views.add_comment, name="add_comment"),
    path("vote/post/<int:pk>/", core_views.vote_post, name="vote_post"),
    path("vote/comment/<int:pk>/", core_views.vote_comment, name="vote_comment"),
    path("r/<slug:name>/submit/", core_views.submit_post, name="submit_post"),
    path("r/<slug:name>/", core_views.community, name="community"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
>>>>>>> e519127d299e92c16c01fb19bd5dd78662494972

