from __future__ import annotations

import html
import logging
import os
import re
import hashlib
from typing import Optional
from urllib.parse import parse_qs, urlparse

from django.core.cache import cache
from django.conf import settings

from ..http_client import fetch_html
from .video_urls import canonicalize_video_url

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
        resp = fetch_html(url, source="og-image")
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
FALLBACK_ALT = "Preview image unavailable"  # alt text for missing thumbnails


def fetch_og_image(url: str) -> Optional[str]:
    """Fetch the OpenGraph image for ``url`` with caching."""

    # During tests we bypass caching to avoid cross-test interference.
    if os.getenv("PYTEST_CURRENT_TEST"):
        result, status = scrape_og_image(url)
        fetch_og_image.last_status = status
        return result

    key = f"{_CACHE_KEY_PREFIX}{url}"
    cached = cache.get(key)
    if cached is not None:
        fetch_og_image.last_status = None
        return None if cached == _CACHE_NONE else cached

    result, status = scrape_og_image(url)
    fetch_og_image.last_status = status
    if status is None or status >= 400:
        return result

    cache.set(key, result or _CACHE_NONE, _CACHE_TIMEOUT)
    return result


fetch_og_image.last_status = None  # type: ignore[attr-defined]


def svg_placeholder(label: str, alt: str | None = None) -> tuple[str, str]:
    """Return a small inline SVG placeholder and its alt text."""
    text = html.escape(label or "")
    alt_text = alt or FALLBACK_ALT
    uri = (
        "data:image/svg+xml;utf8,"
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 675'>"
        "<rect width='1200' height='675' fill='%23e5e5e5'/>"
        f"<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' "
        f"font-family='system-ui, sans-serif' font-size='40' fill='%23666'>{text}</text>"
        "</svg>"
    )
    return uri, alt_text


def youtube_fallback_thumb(url: str, fetch_remote: bool = False) -> str | None:
    """Return a YouTube thumbnail URL if possible.

    When ``fetch_remote`` is ``True`` we try to use the higher resolution
    ``maxresdefault.jpg`` image and fall back to ``hqdefault.jpg`` on 404.
    Without network access we simply return the ``hqdefault.jpg`` URL.
    """

    qs = parse_qs(urlparse(url).query)
    vid = qs.get("v", [None])[0]
    if not vid:
        return None
    base = f"https://i.ytimg.com/vi/{vid}"
    if fetch_remote:
        hi_res = f"{base}/maxresdefault.jpg"
        try:
            resp = fetch_html(hi_res, source="youtube-thumb")
            if resp.status_code != 404:
                return hi_res
        except Exception:
            pass
    return f"{base}/hqdefault.jpg"


def rumble_fallback_thumb(url: str) -> str | None:
    """Return a deterministic CDN thumbnail URL for Rumble if possible."""

    m = re.search(r"/(v[0-9a-z]+)", urlparse(url).path)
    if not m:
        return None
    slug = m.group(1)
    if not re.fullmatch(r"v[0-9a-z]{5,}", slug):
        return None
    # Rumble thumbnails appear to follow a stable pattern under sp.rmbl.ws.
    # If this pattern changes the function should return ``None`` to avoid
    # broken images.
    return f"https://sp.rmbl.ws/s8/1/{slug}.jpg"


def x_fallback_thumb(url: str) -> str | None:
    """Scrape the X status page for a pbs.twimg.com image."""

    try:
        resp = fetch_html(url, source="x-thumb")
        resp.raise_for_status()
    except Exception:
        return None
    match = re.search(r'https://pbs\.twimg\.com/media/[^"]+', resp.text)
    if match:
        return html.unescape(match.group(0))
    return None


_THUMB_KEY_PREFIX = "thumb:"  # cache key prefix for successful lookups
_THUMB_TTL = 60 * 60 * 24  # seconds
_FAIL_KEY_PREFIX = "thumbfail:"  # cache key prefix for failures
_FAIL_TTL = 60 * 15  # seconds
_FAIL_RETRY_TTL = 60  # seconds for throttling errors


def _fail_ttl(status: Optional[int]) -> int:
    """Return cache TTL for failed lookups based on ``status``."""
    if status in {403, 429}:
        return _FAIL_RETRY_TTL
    return _FAIL_TTL


def _provider_fallback(url: str, fetch_remote: bool) -> str | None:
    """Return provider-specific fallback thumbnails."""

    domain = urlparse(url).netloc.lower()
    if "youtube.com" in domain:
        return youtube_fallback_thumb(url, fetch_remote)
    if "rumble.com" in domain:
        return rumble_fallback_thumb(url)
    if fetch_remote and "x.com" in domain:
        return x_fallback_thumb(url)
    return None


_EXTENSION_MAP = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
}


def cache_remote_image(remote_url: str, canon_url: str) -> str | None:
    """Fetch ``remote_url`` and cache locally under a stable name.

    The canonical video URL ``canon_url`` is hashed to derive the filename. A
    previously cached file is returned without fetching the remote again.
    On a fetch failure we return ``None`` so callers can fall back.
    """

    digest = hashlib.sha256(canon_url.encode("utf-8")).hexdigest()
    base = settings.THUMB_CACHE_DIR / digest

    for ext in _EXTENSION_MAP.values():
        candidate = base.with_suffix(f".{ext}")
        if candidate.exists():
            logger.info("rumble-thumb cache %s result=hit", canon_url)
            return f"{settings.MEDIA_URL}thumbs/{candidate.name}"

    status = None
    try:
        resp = fetch_html(remote_url, source="rumble-thumb")
        status = resp.status_code
        resp.raise_for_status()
    except Exception:
        logger.info("rumble-thumb fetch %s status=%s result=fallback", remote_url, status or "error")
        return None

    content_type = resp.headers.get("Content-Type", "").split(";")[0].lower()
    ext = _EXTENSION_MAP.get(content_type)
    if not ext:
        logger.info("rumble-thumb fetch %s status=%s result=fallback", remote_url, status)
        return None

    path = base.with_suffix(f".{ext}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(resp.content)
    logger.info("rumble-thumb fetch %s status=%s result=stored", remote_url, status)
    return f"{settings.MEDIA_URL}thumbs/{path.name}"


def resolve_thumbnail(url: str, label: str, fetch_remote: bool = False) -> tuple[str, str]:
    """Return thumbnail URL and alt text.

    The URL is first canonicalised. We then check caches for a prior
    successful lookup or a recent failure. When ``fetch_remote`` is ``True``
    the OpenGraph image is fetched; if that fails we fall back to
    provider-specific heuristics. A missing thumbnail results in an inline
    SVG placeholder.
    """

    domain = urlparse(url).netloc.lower()
    direct_og = (
        (settings.YT_DIRECT_OG and ("youtube.com" in domain or "youtu.be" in domain))
        or (settings.RUMBLE_DIRECT_OG and "rumble.com" in domain)
        or (
            settings.X_DIRECT_OG
            and domain
            in {
                "x.com",
                "twitter.com",
                "mobile.twitter.com",
                "m.twitter.com",
                "fxtwitter.com",
                "vxtwitter.com",
            }
        )
    )

    canon_url = url if direct_og else canonicalize_video_url(url)

    success_key = f"{_THUMB_KEY_PREFIX}{canon_url}"
    cached = cache.get(success_key)
    if cached:
        return cached, label

    fail_key = f"{_FAIL_KEY_PREFIX}{canon_url}"
    if cache.get(fail_key):
        return svg_placeholder(label)

    thumb = None
    status = None
    if fetch_remote:
        thumb = fetch_og_image(canon_url)
        status = getattr(fetch_og_image, "last_status", None)
        if thumb and direct_og and "rumble.com" in domain:
            cached = cache_remote_image(thumb, canon_url)
            if cached:
                thumb = cached
            else:
                thumb = None
    if not thumb and not direct_og:
        thumb = _provider_fallback(canon_url, fetch_remote)
        if thumb and "rumble.com" in domain:
            if thumb.startswith("https://"):
                cached = cache_remote_image(thumb, canon_url)
                if cached:
                    thumb = cached
                else:
                    thumb = None
            else:
                thumb = None

    if thumb and (thumb.startswith("https://") or thumb.startswith(settings.MEDIA_URL)):
        cache.set(success_key, thumb, _THUMB_TTL)
        return thumb, label

    cache.set(fail_key, True, _fail_ttl(status))
    return svg_placeholder(label)
