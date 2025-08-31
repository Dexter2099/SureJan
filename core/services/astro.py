from datetime import timedelta

from django.conf import settings

from ..models import CommunityBaseline, Post, Vote


def compute_post_signals(post_id):
    """Compute engagement signals for a post.

    Metrics analysed:
    - ``rate5``: votes accrued in the first 5 minutes.
    - ``rate15``: votes accrued in the first 15 minutes.
    - ``early_new_share``: proportion of the first N votes from new accounts.
    - ``discuss_ratio``: comments per 100 upvotes.

    The function returns a dictionary with raw metrics, baseline thresholds,
    boolean flags for anomalies and an aggregated severity score (0-100).
    """

    # Retrieve post, burst state and engagement events in a single query
    post = (
        Post.objects.select_related("community", "burst_state")
        .prefetch_related("engagement_events")
        .get(pk=post_id)
    )
    # access burst state to ensure it exists; not directly used in calculations
    _state = getattr(post, "burst_state", None)  # noqa: F841

    events = [e for e in post.engagement_events.all() if e.event_type == "vote"]

    five = post.created_at + timedelta(minutes=5)
    fifteen = post.created_at + timedelta(minutes=15)

    rate5 = sum(1 for e in events if e.created_at <= five)
    rate15 = sum(1 for e in events if e.created_at <= fifteen)

    # Early new-account share
    early_events = events[: settings.ASTRO_EARLY_VOTES_N]
    early_votes = len(early_events)
    new_votes = sum(
        1 for e in early_events if e.voter_age_days <= settings.ASTRO_NEW_ACCOUNT_DAYS
    )
    early_new_share = new_votes / early_votes if early_votes else 0.0

    # Discussion ratio: comments per 100 upvotes
    upvotes = Vote.objects.filter(
        target_type="post", target_id=post.pk, value=1
    ).count()
    discuss_ratio = (post.comment_count * 100.0 / upvotes) if upvotes else 0.0

    baseline = CommunityBaseline.objects.filter(community=post.community).first()
    base5 = baseline.p95_votes_5m if baseline else 0.0
    base15 = baseline.p95_votes_15m if baseline else 0.0
    base_discuss = baseline.p10_comments_per_100_upvotes if baseline else 0.0

    unusual_5 = rate5 > base5 and base5 > 0
    unusual_15 = rate15 > base15 and base15 > 0
    new_share_red = (
        early_votes >= settings.ASTRO_MIN_EARLY_VOTES
        and early_new_share > settings.ASTRO_EARLY_SHARE_RED
    )
    discuss_low = discuss_ratio < base_discuss and base_discuss > 0

    # --- severity aggregation -------------------------------------------------
    severity = 0.0
    if base5 > 0:
        severity += max(0.0, min(40.0, (rate5 - base5) / base5 * 40.0))
    if base15 > 0:
        severity += max(0.0, min(30.0, (rate15 - base15) / base15 * 30.0))
    if early_votes >= settings.ASTRO_MIN_EARLY_VOTES:
        severity += max(
            0.0,
            min(
                20.0,
                (early_new_share - settings.ASTRO_EARLY_SHARE_RED)
                / max(1e-9, 1 - settings.ASTRO_EARLY_SHARE_RED)
                * 20.0,
            ),
        )
    if base_discuss > 0:
        severity += max(0.0, min(10.0, (base_discuss - discuss_ratio) / base_discuss * 10.0))
    severity = round(min(severity, 100.0), 2)

    return {
        "rate5": rate5,
        "rate15": rate15,
        "early_votes": early_votes,
        "early_new_share": early_new_share,
        "discuss_ratio": discuss_ratio,
        "thresholds": {
            "p95_votes_5m": base5,
            "p95_votes_15m": base15,
            "p10_comments_per_100_upvotes": base_discuss,
            "early_share_red": settings.ASTRO_EARLY_SHARE_RED,
            "min_early_votes": settings.ASTRO_MIN_EARLY_VOTES,
        },
        "flags": {
            "unusual_5": unusual_5,
            "unusual_15": unusual_15,
            "new_share_red": new_share_red,
            "discuss_low": discuss_low,
        },
        "severity": severity,
    }
