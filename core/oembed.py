"""Helper for fetching and sanitizing oEmbed HTML."""

from __future__ import annotations

import re
from urllib.parse import quote, urlparse

import bleach
import requests


def fetch_oembed(url: str) -> dict:
    """Return embed HTML or a fallback link card for ``url``.

    For known providers (YouTube, Rumble and X/Twitter) the provider's oEmbed
    endpoint is queried and the returned HTML is sanitized with Bleach.  On
    failure or for unsupported providers a basic link card with title and
    favicon information is returned.
    """

    providers = {
        "youtube.com": "https://www.youtube.com/oembed?format=json&url=",
        "youtu.be": "https://www.youtube.com/oembed?format=json&url=",
        "rumble.com": "https://rumble.com/api/oembed.json?url=",
        "twitter.com": "https://publish.twitter.com/oembed?omit_script=1&url=",
        "x.com": "https://publish.twitter.com/oembed?omit_script=1&url=",
    }

    parsed = urlparse(url)
    domain = parsed.netloc
    endpoint = None
    for key, base in providers.items():
        if key in domain:
            endpoint = f"{base}{quote(url, safe='')}"
            break

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
            return {"type": "embed", "html": clean, "thumbnail_url": thumb}
        except Exception:
            pass

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
    return {
        "type": "link",
        "url": url,
        "domain": domain,
        "title": title,
        "favicon": favicon,
    }
