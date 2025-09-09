from django.urls import path

from . import views

urlpatterns = [
    path("comment/<int:post_id>/reply/", views.comment_reply, name="comment_reply"),
    path("comment/<int:pk>/reply-form/", views.comment_reply_form, name="comment_reply_form"),
    path("comment/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
    path("comment/<int:pk>/edit/", views.comment_edit, name="comment_edit"),
    path("comments/new", views.comment_new, name="comment_new"),
    path("comments/create", views.comment_create, name="comment_create"),
    path("comments/children", views.comment_children, name="comment_children"),
    path("comments/vote/<int:pk>/", views.vote_comment, name="vote_comment"),
]
