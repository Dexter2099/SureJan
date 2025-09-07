from __future__ import annotations

"""Helpers for normalising video URLs and removing tracking parameters."""

from urllib.parse import parse_qsl, urlparse, urlencode, urlunparse

from .video_urls import canonicalize_video_url, is_rumble_url

# Common tracking parameters to drop from URLs.
_TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "igshid",
}


def cleanup_url(url: str) -> str:
    """Return ``url`` canonicalised with tracking parameters removed.

    The URL is first canonicalised using :func:`canonicalize_video_url`. Query
    parameters used for tracking, such as ``utm_*`` or ``fbclid``, are removed.
    For Rumble URLs all query parameters are dropped entirely.
    """

    url = canonicalize_video_url(url)
    parsed = urlparse(url)

    # Rumble URLs ignore all query parameters.
    if is_rumble_url(url):
        parsed = parsed._replace(query="")
        return urlunparse(parsed)

    qs = parse_qsl(parsed.query, keep_blank_values=True)
    filtered = [
        (k, v)
        for k, v in qs
        if not (k.startswith("utm_") or k in _TRACKING_PARAMS)
    ]
    parsed = parsed._replace(query=urlencode(filtered, doseq=True))
    return urlunparse(parsed)
