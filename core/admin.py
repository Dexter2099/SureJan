from django.contrib import admin

from .models import Community, Post


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "title", "created_at")
    search_fields = ("name", "title")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "community", "author", "post_type", "title", "score", "created_at")
    list_filter = ("post_type", "community")
    search_fields = ("title", "body")
