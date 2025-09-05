from __future__ import annotations

import html
import re
from typing import Optional

import requests

OG_IMAGE_RE = re.compile(r"<meta\s+property=['\"]og:image['\"]\s+content=['\"]([^'\"]+)['\"]", re.IGNORECASE)


def scrape_og_image(url: str) -> Optional[str]:
    """Return the first OpenGraph image URL for ``url`` if present."""
    try:
        resp = requests.get(
            url,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SureJanBot/1.0)"},
        )
        resp.raise_for_status()
    except Exception:
        return None

    match = OG_IMAGE_RE.search(resp.text)
    if match:
        return match.group(1)
    return None


def fetch_og_image(url: str) -> Optional[str]:
    """Fetch the OpenGraph image for ``url``.

    A light wrapper around :func:`scrape_og_image` that is easier to mock in
    tests. Returns ``None`` when no OG image is available or fetching fails.
    """
    return scrape_og_image(url)


def svg_placeholder(label: str) -> str:
    """Return a small inline SVG placeholder data URI with ``label`` text."""
    text = html.escape(label or "")
    return (
        "data:image/svg+xml;utf8,"
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 675'>"
        "<rect width='1200' height='675' fill='%23e5e5e5'/>"
        f"<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' "
        f"font-family='system-ui, sans-serif' font-size='40' fill='%23666'>{text}</text>"
        "</svg>"
    )


def resolve_thumbnail(url: str, label: str) -> str:
    """Return OG image for ``url`` or a placeholder SVG when missing."""
    return scrape_og_image(url) or svg_placeholder(label)
