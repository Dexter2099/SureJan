"""Signal handlers for cache invalidation and comment count consistency."""

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F

from comments.models import Comment
from .models import EngagementEvent, Post


def _cache_key(post_id):
    return f"post_signals:{post_id}"


@receiver(post_save, sender=EngagementEvent)
def engagement_event_saved(sender, instance, **kwargs):
    """Invalidate cached post signals when an engagement event is recorded."""
    cache.delete(_cache_key(instance.post_id))


@receiver(post_save, sender=Comment)
def comment_created(sender, instance, created, **kwargs):
    """On comment create: invalidate cache and increment Post.comment_count."""
    if created:
        Post.objects.filter(pk=instance.post_id).update(
            comment_count=F("comment_count") + 1
        )
        cache.delete(_cache_key(instance.post_id))


@receiver(post_save, sender=Comment)
def comment_deleted(sender, instance, created, **kwargs):
    """Invalidate cached post signals when a comment is soft-deleted."""
    if not created:
        update_fields = kwargs.get("update_fields")
        if update_fields and "is_deleted" in update_fields and instance.is_deleted:
            cache.delete(_cache_key(instance.post_id))


@receiver(post_delete, sender=Comment)
def comment_hard_deleted(sender, instance, **kwargs):
    """On hard delete: decrement Post.comment_count and invalidate cache.

    This fires once per deleted Comment row (including cascaded descendants),
    so applying a -1 per row keeps the counter in sync with the actual table.
    """
    Post.objects.filter(pk=instance.post_id).update(
        comment_count=F("comment_count") - 1
    )
    cache.delete(_cache_key(instance.post_id))
