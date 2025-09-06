from __future__ import annotations

"""Utilities for building provider-specific embed iframes."""

import re
from urllib.parse import parse_qs, urlparse

from django.utils.safestring import mark_safe

from .video_urls import canonicalize_video_url


_DEF_IFRAME_ATTRS = (
    'loading="lazy" '
    'allowfullscreen '
    'referrerpolicy="no-referrer" '
    'width="640" height="360"'
)


def _iframe(src: str) -> str:
    """Return a safe iframe element for ``src``."""
    html = f'<iframe src="{src}" {_DEF_IFRAME_ATTRS}></iframe>'
    return mark_safe(html)


def build_embed_iframe(url: str | None) -> str | None:
    """Return iframe HTML for ``url`` or ``None`` if not embeddable.

    The URL is first canonicalised to simplify provider detection. Only a
    small set of well-known providers are supported. Unknown providers
    return ``None`` which allows callers to fall back to a link card.
    """
    if not url:
        return None

    canon = canonicalize_video_url(url)
    parsed = urlparse(canon)
    domain = parsed.netloc.lower()

    if domain == "youtube.com":
        vid = parse_qs(parsed.query).get("v", [None])[0]
        if vid:
            return _iframe(f"https://www.youtube.com/embed/{vid}")
        return None

    if domain == "rumble.com":
        slug = parsed.path.lstrip("/")
        if re.fullmatch(r"v[0-9a-z]+", slug):
            return _iframe(f"https://rumble.com/embed/{slug}")
        return None

    if domain == "x.com":
        m = re.search(r"/status/(\d+)", parsed.path)
        if m:
            tweet_id = m.group(1)
            src = f"https://platform.twitter.com/embed/Tweet.html?id={tweet_id}"
            return _iframe(src)
        return None

    return None
