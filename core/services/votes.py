from datetime import timedelta

from django.utils import timezone

from ..models import Comment, EngagementEvent, Post, PostBurstState
from ..votes import apply_vote as core_apply_vote


def apply_vote(user, target_type, target_id, value):
    """Apply a vote and record engagement/burst data.

    Returns the tuple ``(delta_score, old_value, new_value)`` from the core
    voting service. Side effects are only triggered when ``delta_score`` is
    non-zero (i.e. the author's net score changes).
    """
    delta, old, new = core_apply_vote(user, target_type, target_id, value)
    if delta != 0:
        post = _get_post(target_type, target_id)
        _record_engagement_event(post, user)
        _update_post_burst_state(post)
    return delta, old, new


def _get_post(target_type, target_id):
    if target_type == "post":
        return Post.objects.get(pk=target_id)
    comment = Comment.objects.select_related("post").get(pk=target_id)
    return comment.post


def _record_engagement_event(post, voter):
    now = timezone.now()
    age_days = min((now - voter.date_joined).days, 3650)
    EngagementEvent.objects.create(
        post=post, event_type="vote", voter_age_days=age_days
    )


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
