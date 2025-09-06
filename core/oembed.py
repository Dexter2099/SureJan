"""Helper for fetching and sanitizing oEmbed HTML."""

from __future__ import annotations

import re
from urllib.parse import quote, urlparse

from django.conf import settings
from django.core.cache import cache

import bleach
import requests


_CACHE_KEY_PREFIX = "oembed:"
_CACHE_TIMEOUT = 60 * 60  # 1 hour


def fetch_oembed(url: str) -> dict:
    """Return embed HTML or a fallback link card for ``url`` with caching."""

    key = f"{_CACHE_KEY_PREFIX}{url}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    providers = {
        "youtube.com": "https://www.youtube.com/oembed?format=json&url=",
        "youtu.be": "https://www.youtube.com/oembed?format=json&url=",
        "rumble.com": "https://rumble.com/api/oembed.json?url=",
    }
    if settings.ENABLE_TWITTER_EMBEDS:
        providers.update(
            {
                "twitter.com": "https://publish.twitter.com/oembed?omit_script=1&url=",
                "x.com": "https://publish.twitter.com/oembed?omit_script=1&url=",
            }
        )

    parsed = urlparse(url)
    domain = parsed.netloc
    endpoint = None
    for key_, base in providers.items():
        if key_ in domain:
            endpoint = f"{base}{quote(url, safe='')}"
            break

    result = None
    if endpoint:
        try:
            resp = requests.get(endpoint, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            html = data.get("html", "")
            thumb = data.get("thumbnail_url")
            clean = bleach.clean(
                html,
                tags=[
                    "iframe",
                    "blockquote",
                    "a",
                    "p",
                    "span",
                    "img",
                    "br",
                    "div",
                ],
                attributes={
                    "iframe": [
                        "src",
                        "width",
                        "height",
                        "frameborder",
                        "allow",
                        "allowfullscreen",
                    ],
                    "blockquote": ["class", "data-theme"],
                    "a": ["href", "class"],
                    "img": ["src", "alt"],
                    "div": ["class"],
                },
                strip=True,
            )
            result = {"type": "embed", "html": clean, "thumbnail_url": thumb}
        except Exception:
            pass

    if not result:
        # Fallback simple link card
        title = None
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            match = re.search(r"<title>(.*?)</title>", resp.text, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip()
        except Exception:
            pass
        favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
        result = {
            "type": "link",
            "url": url,
            "domain": domain,
            "title": title,
            "favicon": favicon,
        }

    cache.set(key, result, _CACHE_TIMEOUT)
    return result
