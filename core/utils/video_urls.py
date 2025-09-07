from __future__ import annotations

"""Utilities for canonicalising common video URLs."""

import re
from urllib.parse import parse_qs, urlparse, urlunparse


_YT_PATTERNS = [
    r"v=([\w-]+)",
    r"youtu\.be/([\w-]+)",
    r"embed/([\w-]+)",
    r"shorts/([\w-]+)",
]


def canonicalize_youtube(url: str) -> str | None:
    """Return canonical ``https://youtube.com/watch?v=...`` for YouTube URLs."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "youtube" not in host and "youtu.be" not in host:
        return None

    vid = None
    if host.endswith("youtu.be"):
        vid = parsed.path.lstrip("/")
    else:
        qs = parse_qs(parsed.query).get("v")
        if qs:
            vid = qs[0]
        if not vid:
            m = re.search(r"/(?:embed|shorts)/([\w-]+)", parsed.path)
            if m:
                vid = m.group(1)
    if not vid:
        return None
    return f"https://youtube.com/watch?v={vid}"


def is_rumble_url(url: str) -> bool:
    """Return ``True`` if ``url`` points to rumble.com."""
    host = urlparse(url).netloc.lower().lstrip("www.")
    return host == "rumble.com"


def canonicalize_rumble_url(url: str) -> str | None:
    """Return canonical ``https://rumble.com/v...-slug.html`` for Rumble URLs."""
    if not is_rumble_url(url):
        return None
    parsed = urlparse(url)
    path = parsed.path
    if path.startswith("/embed/"):
        path = "/" + path[len("/embed/"):]
    m = re.search(r"/(v[0-9a-z]+(?:-[\w-]+)?)", path)
    if not m:
        return None
    slug = m.group(1)
    if not slug.endswith(".html"):
        slug += ".html"
    return f"https://rumble.com/{slug}"


def canonicalize_x(url: str) -> str | None:
    """Return canonical ``https://x.com/...`` URL for X/Twitter links."""
    parsed = urlparse(url)
    host = parsed.netloc.lower().lstrip("www.")
    if host not in {
        "x.com",
        "twitter.com",
        "mobile.twitter.com",
        "m.twitter.com",
        "fxtwitter.com",
        "vxtwitter.com",
    }:
        return None
    path = parsed.path.rstrip("/")
    return urlunparse(("https", "x.com", path, "", "", ""))


_CANONICALIZERS = [canonicalize_youtube, canonicalize_rumble_url, canonicalize_x]


def canonicalize_video_url(url: str) -> str:
    """Return canonical form of ``url`` for known video providers."""
    for fn in _CANONICALIZERS:
        result = fn(url)
        if result:
            return result
    return url
