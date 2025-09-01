"""Simple per-user rate limiting decorator using Django cache."""

from functools import wraps
from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from .models import get_points, RateLimitCounter


def _is_new_user(user):
    return (timezone.now() - user.date_joined) < timedelta(hours=24) or get_points(user) == 0


def ratelimit(*, key="user", action: str, limit, window: int = 60):
    """Limit ``action`` executions per ``window`` seconds.

    ``limit`` may be an ``int`` or a ``(new_limit, old_limit)`` tuple. When a
    tuple is supplied the user's signup age determines which limit applies.

    Only ``key='user'`` is supported. The caller must ensure the user is
    authenticated. When the limit is exceeded a ``429`` response is returned.
    If the request originated from HTMX a small message partial is rendered.
    A ``Retry-After`` header is included so clients know when to retry.
    """

    if key != "user":
        raise ValueError("Only user-based rate limiting is supported")

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            # Only count POST requests that actually perform the action.
            if request.method != "POST":
                return view_func(request, *args, **kwargs)

            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)

            limit_value = limit
            if isinstance(limit, tuple):
                new_limit, old_limit = limit
                limit_value = new_limit if _is_new_user(request.user) else old_limit

            now = timezone.now()
            counter, _ = RateLimitCounter.objects.get_or_create(
                user=request.user,
                action=action,
                defaults={"period_start": now},
            )
            if now - counter.period_start >= timedelta(seconds=window):
                counter.count = 0
                counter.period_start = now

            if counter.count >= limit_value:
                context = {"action": action, "retry_after": window}
                if request.headers.get("HX-Request") == "true":
                    resp = render(
                        request, "core/partials/ratelimit.html", context, status=429
                    )
                else:
                    resp = render(request, "429.html", context, status=429)
                resp.headers["Retry-After"] = str(window)
                return resp

            counter.count += 1
            counter.save(update_fields=["count", "period_start"])

            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
