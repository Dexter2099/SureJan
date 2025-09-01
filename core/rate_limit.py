"""Per-user action rate limiting utilities."""

from datetime import timedelta

from django.utils import timezone

from .models import RateLimitCounter, get_points


def _is_new_user(user):
    return (timezone.now() - user.date_joined) < timedelta(hours=24) or get_points(user) == 0


def check_rate_limit(user, action: str, limit, window: int = 60):
    """Return (limited, retry_after) for ``action`` within ``window`` seconds.

    ``limit`` may be an ``int`` or ``(new_limit, old_limit)`` tuple where the
    first value applies to new users and the second to established users.
    ``retry_after`` is the remaining number of seconds until the window resets
    when ``limited`` is True.
    """

    if not user.is_authenticated:
        return False, 0

    limit_value = limit
    if isinstance(limit, tuple):
        new_limit, old_limit = limit
        limit_value = new_limit if _is_new_user(user) else old_limit

    now = timezone.now()
    counter, _ = RateLimitCounter.objects.get_or_create(
        user=user, action=action, defaults={"period_start": now}
    )
    elapsed = (now - counter.period_start).total_seconds()
    if elapsed >= window:
        counter.count = 0
        counter.period_start = now
        elapsed = 0

    if counter.count >= limit_value:
        retry_after = max(int(window - elapsed), 0)
        return True, retry_after

    counter.count += 1
    counter.save(update_fields=["count", "period_start"])
    return False, 0
