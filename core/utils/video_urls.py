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


def canonicalize_rumble(url: str) -> str | None:
    """Return canonical Rumble URL of the form ``https://rumble.com/v...``."""
    parsed = urlparse(url)
    host = parsed.netloc.lower().lstrip("www.")
    if host != "rumble.com":
        return None
    path = parsed.path
    if path.startswith("/embed/"):
        path = "/" + path[len("/embed/"):]
    m = re.search(r"/(v[0-9a-z]+)", path)
    if not m:
        return None
    slug = m.group(1)
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


_CANONICALIZERS = [canonicalize_youtube, canonicalize_rumble, canonicalize_x]


def canonicalize_video_url(url: str) -> str:
    """Return canonical form of ``url`` for known video providers."""
    for fn in _CANONICALIZERS:
        result = fn(url)
        if result:
            return result
    return url
