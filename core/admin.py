from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Post,
    UserProfile,
    Report,
    EngagementEvent,
    PostBurstState,
)
from comments.models import Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "community",
        "author",
        "post_type",
        "title",
        "heading",
        "body",
        "content_url",
        "link_domain",
        "score",
        "hot_rank",
        "created_at",
    )
    list_filter = ("post_type", "community")
    search_fields = ("title", "heading", "body", "content_url", "link_domain")
    readonly_fields = (
        "score",
        "hot_rank",
        "rising_rank",
        "controversy",
        "best_rank",
        "comment_count",
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "author", "score", "created_at")
    readonly_fields = ("score",)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fields = ("points_cached", "is_banned")
    readonly_fields = ("points_cached",)


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]


try:
    admin.site.unregister(get_user_model())
except admin.sites.NotRegistered:
    pass
admin.site.register(get_user_model(), UserAdmin)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "reporter", "content_type", "object_id", "created_at")
    list_filter = ("content_type", "reporter")


@admin.register(EngagementEvent)
class EngagementEventAdmin(admin.ModelAdmin):
    list_filter = ("post", "post__community")


@admin.register(PostBurstState)
class PostBurstStateAdmin(admin.ModelAdmin):
    list_filter = ("post__community",)


