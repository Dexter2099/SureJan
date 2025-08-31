"""Signal handlers for cache invalidation of post engagement signals."""

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Comment, EngagementEvent


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


@receiver(post_delete, sender=Comment)
def comment_deleted(sender, instance, **kwargs):
    """Invalidate cached post signals when a comment is deleted."""
    cache.delete(_cache_key(instance.post_id))

