"""Shared helper functions for views."""

from datetime import timedelta

from django.core.validators import MaxLengthValidator
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django_ratelimit.core import is_ratelimited


def _is_banned(user):
    """Return True if the user is banned."""
    return getattr(getattr(user, "profile", None), "is_banned", False)


def is_new_user(u):
    """Determine whether a user account is less than 24 hours old."""
    if not u.is_authenticated:
        return True
    return (timezone.now() - u.date_joined) < timedelta(hours=24)


def limit_or_429(request, group, rate):
    """Return whether a request should be rate limited."""
    return is_ratelimited(
        request,
        group=group,
        key="user",
        rate=rate,
        method=["POST"],
        increment=True,
    )


def _find_offending_field(form):
    """Identify the field that exceeds the allowed length in a form."""
    for name, field in form.fields.items():
        value = form.data.get(name)
        if value is None:
            continue
        try:
            length = len(value)
        except TypeError:
            continue
        maxlen = getattr(field, "max_length", None)
        if maxlen and length > maxlen:
            return name, length
        for validator in field.validators:
            if isinstance(validator, MaxLengthValidator) and length > validator.limit_value:
                return name, length
    return "unknown", 0


SORT_TABS = [
    ("hot", "HOT"),
    ("new", "NEW"),
    ("top", "TOP"),
    ("wiki", "WIKI"),
]


def _render_posts(request, posts, next_page, show_community=False, sort_query=""):
    """Render a list of posts and optional pagination link."""
    html = render_to_string(
        "core/partials/post_list.html",
        {
            "posts": posts,
            "show_community": show_community,
            "next_page": next_page,
            "sort_query": sort_query,
        },
        request=request,
    )
    return HttpResponse(html)


__all__ = [
    "_is_banned",
    "is_new_user",
    "limit_or_429",
    "_find_offending_field",
    "SORT_TABS",
    "_render_posts",
]

