"""Vote application service functions."""

from django.db import transaction

from .models import Vote  # models: Post and Comment imported lazily via signals


def apply_vote(user, target_type, target_id, value):
    """Apply a vote and return (delta_score, old_value, new_value).

    The returned ``delta_score`` represents the change applied to the target's
    score. ``old_value`` and ``new_value`` represent the previous and new vote
    values (0 if no vote).
    """
    if value not in (-1, 1):
        raise ValueError("Invalid vote value")

    with transaction.atomic():
        try:
            vote = Vote.objects.select_for_update().get(
                user=user, target_type=target_type, target_id=target_id
            )
            old_value = vote.value
            if old_value == value:
                vote.delete()
                new_value = 0
            else:
                vote.value = value
                vote.save(update_fields=["value"])
                new_value = value
        except Vote.DoesNotExist:
            Vote.objects.create(
                user=user,
                target_type=target_type,
                target_id=target_id,
                value=value,
            )
            old_value = 0
            new_value = value

    delta_score = new_value - old_value
    return delta_score, old_value, new_value
