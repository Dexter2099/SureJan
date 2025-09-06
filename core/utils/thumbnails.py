from __future__ import annotations

import html
import logging
import os
import re
from typing import Optional
from urllib.parse import urlparse

from django.core.cache import cache

from ..http_client import fetch_html

OG_IMAGE_RE = re.compile(
    r"<meta\s+property=['\"]og:image['\"]\s+content=['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)

logger = logging.getLogger(__name__)


def scrape_og_image(url: str) -> tuple[Optional[str], Optional[int]]:
    """Return the first OpenGraph image URL for ``url`` if present."""
    domain = urlparse(url).netloc
    status = None
    try:
        resp = fetch_html(url)
        status = resp.status_code
        resp.raise_for_status()
    except Exception:
        logger.info("og-image fetch %s status=%s result=fallback", domain, status or "error")
        return None, status

    match = OG_IMAGE_RE.search(resp.text)
    if match:
        logger.info("og-image fetch %s status=%s result=image", domain, status)
        return match.group(1), status

    logger.info("og-image fetch %s status=%s result=fallback", domain, status)
    return None, status


_CACHE_KEY_PREFIX = "og-image:"  # cache key prefix for og image lookups
# Cache successful lookups briefly; errors should not be cached.
_CACHE_TIMEOUT = 60  # seconds
_CACHE_NONE = ""  # sentinel value for cached misses


def fetch_og_image(url: str) -> Optional[str]:
    """Fetch the OpenGraph image for ``url`` with caching."""

    # During tests we bypass caching to avoid cross-test interference.
    if os.getenv("PYTEST_CURRENT_TEST"):
        return scrape_og_image(url)[0]

    key = f"{_CACHE_KEY_PREFIX}{url}"
    cached = cache.get(key)
    if cached is not None:
        return None if cached == _CACHE_NONE else cached

    result, status = scrape_og_image(url)
    if status is None or status >= 400:
        return result

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
