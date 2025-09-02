from __future__ import annotations

import re
from urllib.parse import urlparse

from django.conf import settings
from django.utils.html import escape

from core.oembed import fetch_oembed


def build_embed_html(url: str) -> str:
    """Return safe embed placeholder HTML or a link card for ``url``.

    Supports YouTube, Rumble, and Twitter/X embeds rendered behind a click-to-
    play consent gate. Unrecognized providers fall back to a simple link card.
    """
    if not url:
        return ""

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    try:
        data = fetch_oembed(url)
    except Exception:
        data = {}

    if data.get("type") != "embed":
        return (
            f'<div class="link-card"><a href="{escape(url)}" '
            f'rel="noopener nofollow">{escape(parsed.netloc)}</a></div>'
        )

    thumb = data.get("thumbnail_url", "")
    html = data.get("html", "")

    src = ""
    if "youtube" in domain:
        vid = None
        for pattern in [r"v=([\w-]{11})", r"be/([\w-]{11})", r"embed/([\w-]{11})"]:
            m = re.search(pattern, url)
            if m:
                vid = m.group(1)
                break
        if not vid:
            m = re.search(r"embed/([\w-]{11})", html)
            if m:
                vid = m.group(1)
        if not vid:
            return (
                f'<div class="link-card"><a href="{escape(url)}" '
                f'rel="noopener nofollow">{escape(parsed.netloc)}</a></div>'
            )
        if not thumb:
            thumb = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        src = f"https://www.youtube-nocookie.com/embed/{vid}"
    elif "rumble.com" in domain:
        m = re.search(r'src="([^"]+)"', html)
        if not m:
            return (
                f'<div class="link-card"><a href="{escape(url)}" '
                f'rel="noopener nofollow">{escape(parsed.netloc)}</a></div>'
            )
        src = m.group(1)
    elif "twitter.com" in domain or "x.com" in domain:
        if not getattr(settings, "ENABLE_TWITTER_EMBEDS", False):
            return (
                f'<div class="link-card"><a href="{escape(url)}" '
                f'rel="noopener nofollow">{escape(parsed.netloc)}</a></div>'
            )
        m = re.search(r"status/(\d+)", url)
        if not m:
            return (
                f'<div class="link-card"><a href="{escape(url)}" '
                f'rel="noopener nofollow">{escape(parsed.netloc)}</a></div>'
            )
        src = f"https://platform.twitter.com/embed/Tweet.html?id={m.group(1)}"
    else:
        return (
            f'<div class="link-card"><a href="{escape(url)}" '
            f'rel="noopener nofollow">{escape(parsed.netloc)}</a></div>'
        )

    thumb_html = (
        f'<img src="{escape(thumb)}" alt="" loading="lazy" decoding="async" '
        'referrerpolicy="no-referrer" '
        'style="width:100%;height:100%;object-fit:cover;">'
        if thumb
        else ""
    )

    return (
        f'<div class="post-embed" data-src="{escape(src)}" '
        'style="position:relative;padding-top:56.25%;overflow:hidden;">'
        f'<a href="{escape(url)}" rel="noopener nofollow" '
        'style="position:absolute;top:0;left:0;width:100%;height:100%;display:block;">'
        f'{thumb_html}</a></div>'
    )
