from datetime import timedelta
from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def can_author_delete(post, user):
    """Staff can always delete. Author can delete within 15 minutes. Not if already deleted."""
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_staff", False):
        return True
    if getattr(post, "is_deleted", False):
        return False
    if getattr(post, "author_id", None) != getattr(user, "id", None):
        return False
    created = getattr(post, "created_at", None)
    if not created:
        return False
    return timezone.now() - created <= timedelta(minutes=15)


@register.filter
def can_edit_comment(comment, user):
    """Return True if the user may edit the comment within 15 minutes."""
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(comment, "author_id", None) != getattr(user, "id", None):
        return False
    created = getattr(comment, "created_at", None)
    if not created:
        return False
    return timezone.now() - created <= timedelta(minutes=15)
