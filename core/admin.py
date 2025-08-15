"""Admin registrations for core models."""

from django.contrib import admin

from . import models


@admin.register(models.Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "title", "created_at")
    search_fields = ("name", "title")


@admin.register(models.Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "community")


@admin.register(models.Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "file", "created_at")


@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "community",
        "author",
        "post_type",
        "title",
        "score",
        "created_at",
    )
    search_fields = ("title", "body")
    list_filter = ("post_type", "community")


@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "author", "score", "created_at")
    search_fields = ("body",)


@admin.register(models.Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "target_type", "target_id", "value")


