from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Community,
    Post,
    Comment,
    Vote,
    UserProfile,
    Report,
    EngagementEvent,
    PostBurstState,
    CommunityBaseline,
)


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("slug", "title", "is_system")
    list_filter = ("is_system",)
    search_fields = ("slug", "title")

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_system and "slug" not in ro:
            ro.append("slug")
        return ro

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def delete_model(self, request, obj):
        if obj.is_system:
            self.message_user(
                request, "System communities cannot be deleted.", level=messages.ERROR
            )
            return
        return super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        if queryset.filter(is_system=True).exists():
            self.message_user(
                request,
                "Selection includes system communities; deletion aborted.",
                level=messages.ERROR,
            )
            return
        return super().delete_queryset(request, queryset)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "community",
        "author",
        "post_type",
        "title",
        "score",
        "hot_rank",
        "created_at",
    )
    list_filter = ("post_type", "community")
    search_fields = ("title", "body")
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


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "target_type", "target_id", "value")


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fields = ("points_cached", "is_banned")
    readonly_fields = ("points_cached",)


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]


admin.site.unregister(get_user_model())
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


@admin.register(CommunityBaseline)
class CommunityBaselineAdmin(admin.ModelAdmin):
    list_filter = ("community",)
