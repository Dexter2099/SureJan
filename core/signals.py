"""Signal handlers for cache invalidation of post engagement signals."""

from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from comments.models import Comment
from .models import EngagementEvent


def _cache_key(post_id):
    return f"post_signals:{post_id}"


@receiver(post_save, sender=EngagementEvent)
def engagement_event_saved(sender, instance, **kwargs):
    """Invalidate cached post signals when an engagement event is recorded."""
    cache.delete(_cache_key(instance.post_id))


@receiver(post_save, sender=Comment)
def comment_created(sender, instance, created, **kwargs):
    """Invalidate cached post signals when a comment is created."""
    if created:
        cache.delete(_cache_key(instance.post_id))


@receiver(post_save, sender=Comment)
def comment_deleted(sender, instance, created, **kwargs):
    """Invalidate cached post signals when a comment is soft-deleted."""
    if not created:
        update_fields = kwargs.get("update_fields")
        if update_fields and "is_deleted" in update_fields and instance.is_deleted:
            cache.delete(_cache_key(instance.post_id))

