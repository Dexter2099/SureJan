from datetime import timedelta

from django.conf import settings
codex/cache-compute_post_signals-results
from django.core.cache import cache

from django.utils import timezone
main

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

    cache_key = f"post_signals:{post_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

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
    data = {
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
codex/cache-compute_post_signals-results
    cache.set(cache_key, data, 30)
    return data



def compute_user_post_summary(user_id, days: int = 90):
    """Return aggregate post signal stats for a user.

    Looks at posts authored by ``user_id`` within the last ``days`` days and
    computes:

    - percentage of posts that were flagged (severity > 0)
    - average severity across all posts
    - a simple rating bucket based on the average severity

    The function also returns a list of severities in chronological order which
    can be used to render a sparkline in templates.
    """

    since = timezone.now() - timedelta(days=days)
    posts = Post.objects.filter(author_id=user_id, created_at__gte=since).order_by(
        "created_at"
    )
    total = posts.count()
    severities = []
    flagged = 0

    for post in posts:
        signals = compute_post_signals(post.pk)
        severity = signals.get("severity", 0.0)
        severities.append(severity)
        if severity > 0:
            flagged += 1

    pct_flagged = (flagged / total * 100.0) if total else 0.0
    avg_severity = (sum(severities) / total) if total else 0.0

    if avg_severity > 60:
        rating = "red"
    elif avg_severity >= 25:
        rating = "amber"
    else:
        rating = "green"

    return {
        "total_posts": total,
        "flagged_pct": round(pct_flagged, 2),
        "avg_severity": round(avg_severity, 2),
        "rating": rating,
        "severities": severities,
    }
main
