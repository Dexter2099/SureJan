"""Vote application service functions."""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Comment, EngagementEvent, Post, PostBurstState, Vote


def apply_vote(user, target_type, target_id, value):
    """Apply a vote and record engagement/burst data.

    Returns ``(delta_score, old_value, new_value)`` where ``delta_score`` is the
    change applied to the target's score. ``old_value`` and ``new_value`` are the
    previous and new vote values (``0`` if no vote). Side effects are only
    triggered when ``delta_score`` is non-zero.
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
    if delta_score != 0:
        post = _get_post(target_type, target_id)
        _record_engagement_event(post, user)
        _update_post_burst_state(post)
    return delta_score, old_value, new_value


def _get_post(target_type, target_id):
    if target_type == "post":
        return Post.objects.get(pk=target_id)
    comment = Comment.objects.select_related("post").get(pk=target_id)
    return comment.post


def _record_engagement_event(post, voter):
    now = timezone.now()
    age_days = min((now - voter.date_joined).days, 3650)
    EngagementEvent.objects.create(post=post, event_type="vote", voter_age_days=age_days)


def _update_post_burst_state(post):
    now = timezone.now()
    state, _ = PostBurstState.objects.get_or_create(
        post=post,
        defaults={
            "window_start": now,
            "buckets": [0] * 10,
            "bucket_index": 0,
            "total_5m": 0,
        },
    )

    buckets = list(state.buckets or [])
    if len(buckets) < 10:
        buckets += [0] * (10 - len(buckets))

    span = state.bucket_span_seconds
    index = int((now - state.window_start).total_seconds() // span)

    if index >= 10 or index < 0:
        if index >= 10:
            shift = min(index, 10)
            if shift >= 10:
                buckets = [0] * 10
            else:
                buckets = buckets[shift:] + [0] * shift
            state.window_start += timedelta(seconds=shift * span)
        else:
            buckets = [0] * 10
            state.window_start = now
        index = int((now - state.window_start).total_seconds() // span)
        if index >= 10 or index < 0:
            buckets = [0] * 10
            state.window_start = now
            index = 0

    buckets[index] += 1
    state.buckets = buckets
    state.bucket_index = index
    total = 0
    for i in range(5):
        total += buckets[(index - i) % 10]
    state.total_5m = total
    state.save(
        update_fields=[
            "buckets",
            "bucket_index",
            "window_start",
            "total_5m",
            "last_updated",
        ]
    )
