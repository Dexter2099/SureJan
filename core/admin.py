from django.contrib import admin

from .models import Community, Post, Comment, Vote, UserProfile


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name", "title", "created_at")
    search_fields = ("slug", "name", "title")


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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "points_cached")
