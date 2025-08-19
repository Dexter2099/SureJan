"""Simple per-user rate limiting decorator using Django cache."""

from functools import wraps
from django.core.cache import cache
from django.http import HttpResponse
from django.template.loader import render_to_string


def ratelimit(*, key="user", action: str, limit: int, window: int = 60):
    """Limit ``action`` executions per ``window`` seconds for the given key.

    Only ``key='user'`` is supported. The caller must ensure the user is
    authenticated. When the limit is exceeded a ``429`` response is returned.
    If the request originated from HTMX a small message partial is rendered.
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

            cache_key = f"rl:{action}:{request.user.pk}"
            count = cache.get(cache_key, 0)
            if count >= limit:
                if request.headers.get("HX-Request") == "true":
                    html = render_to_string(
                        "core/partials/ratelimit.html", {"action": action}, request=request
                    )
                    return HttpResponse(html, status=429)
                return HttpResponse("Too many requests", status=429)

            if count == 0:
                cache.add(cache_key, 1, window)
            else:
                cache.incr(cache_key)

            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator

