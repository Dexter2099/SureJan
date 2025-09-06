from __future__ import annotations

import html
import re
from typing import Optional

import os
from django.core.cache import cache
import requests

OG_IMAGE_RE = re.compile(r"<meta\s+property=['\"]og:image['\"]\s+content=['\"]([^'\"]+)['\"]", re.IGNORECASE)

# Headers used when scraping remote pages for OpenGraph images. A realistic
# browser-like User-Agent and Accept-Language help avoid some bot protections.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_og_image(url: str) -> Optional[str]:
    """Return the first OpenGraph image URL for ``url`` if present."""
    try:
        resp = requests.get(url, timeout=5, headers=REQUEST_HEADERS)
        resp.raise_for_status()
    except Exception:
        return None

    match = OG_IMAGE_RE.search(resp.text)
    if match:
        return match.group(1)
    return None


_CACHE_KEY_PREFIX = "og-image:"  # cache key prefix for og image lookups
_CACHE_TIMEOUT = 60 * 60  # 1 hour
_CACHE_NONE = ""  # sentinel value for cached misses


def fetch_og_image(url: str) -> Optional[str]:
    """Fetch the OpenGraph image for ``url`` with caching."""

    # During tests we bypass caching to avoid cross-test interference.
    if os.getenv("PYTEST_CURRENT_TEST"):
        return scrape_og_image(url)

    key = f"{_CACHE_KEY_PREFIX}{url}"
    cached = cache.get(key)
    if cached is not None:
        return None if cached == _CACHE_NONE else cached

    result = scrape_og_image(url)
    cache.set(key, result or _CACHE_NONE, _CACHE_TIMEOUT)
    return result


def svg_placeholder(label: str, alt: str | None = None) -> tuple[str, str]:
    """Return a small inline SVG placeholder and its alt text."""
    text = html.escape(label or "")
    alt_text = alt or "Preview image unavailable"
    uri = (
        "data:image/svg+xml;utf8,"
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 675'>"
        "<rect width='1200' height='675' fill='%23e5e5e5'/>"
        f"<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' "
        f"font-family='system-ui, sans-serif' font-size='40' fill='%23666'>{text}</text>"
        "</svg>"
    )
    return uri, alt_text


def resolve_thumbnail(url: str, label: str) -> tuple[str, str]:
    """Return OG image and alt text or a placeholder when missing."""
    og = fetch_og_image(url)
    if og:
        return og, label
    return svg_placeholder(label)
