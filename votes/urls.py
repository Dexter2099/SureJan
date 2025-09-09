from django.urls import path

from . import views

urlpatterns = [
    path("posts/vote/<int:pk>/", views.vote_post, name="vote_post"),
    path("comments/vote/<int:pk>/", views.vote_comment, name="vote_comment"),
]
