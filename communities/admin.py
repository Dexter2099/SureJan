from django.contrib import admin, messages

from .models import Community, CommunityBaseline


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


@admin.register(CommunityBaseline)
class CommunityBaselineAdmin(admin.ModelAdmin):
    list_filter = ("community",)

