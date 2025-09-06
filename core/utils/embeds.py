from __future__ import annotations

import re
from urllib.parse import urlparse

from django.conf import settings
from django.utils.html import escape

from core.oembed import fetch_oembed
from core.utils.thumbnails import fetch_og_image, svg_placeholder


def build_embed_html(url: str) -> str:
    """Return safe embed placeholder HTML or a link card for ``url``.

    Supports YouTube, Rumble, and Twitter/X embeds rendered behind a click-to-
    play consent gate. Unrecognized providers fall back to a simple link card.
    oEmbed and OpenGraph image lookups are cached to reduce repeated network
    requests.
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

    html = data.get("html", "")

    thumb = data.get("thumbnail_url") or fetch_og_image(url)
    thumb_alt = "Preview image unavailable"

    src = ""
    placeholder_label = "Preview"
    vid = None
    if "youtube" in domain:
        for pattern in [r"v=([\w-]+)", r"be/([\w-]+)", r"embed/([\w-]+)"]:
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
        src = f"https://www.youtube-nocookie.com/embed/{vid}"
        placeholder_label = "YouTube preview"
    elif "rumble.com" in domain:
        # 1) Try to read iframe src from the provider HTML (support " and ' quotes)
        m = re.search(r"src=['\"]([^'\"]+)['\"]", html or "")
        src = m.group(1) if m else ""

        # 2) If no src in HTML, try to derive an embed id from the URL like:
        #    https://rumble.com/vxyz-test.html  -> id: vxyz
        #    Fallback to building https://rumble.com/embed/<id>/ if we find one
        if not src:
            m2 = re.search(r"/(v[\w]+)[-\.]", url)  # captures vxyz from /vxyz-test.html
            if m2:
                src = f"https://rumble.com/embed/{m2.group(1)}/"

        # If still no usable src, degrade to a plain link card
        if not src:
            return (
                f'<div class="link-card"><a href="{escape(url)}" '
                f'rel="noopener nofollow">{escape(parsed.netloc)}</a></div>'
            )
        placeholder_label = "Rumble preview"
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
        placeholder_label = "Tweet preview"
    else:
        return (
            f'<div class="link-card"><a href="{escape(url)}" '
            f'rel="noopener nofollow">{escape(parsed.netloc)}</a></div>'
        )
    if not thumb and "youtube" in domain and vid:
        thumb = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        thumb_alt = placeholder_label
    if not thumb:
        thumb, thumb_alt = svg_placeholder(placeholder_label, placeholder_label)
    else:
        thumb_alt = placeholder_label
    if thumb.startswith("http://"):
        thumb = "https://" + thumb[len("http://") :]

    return (
        f'<div class="post-embed" data-src="{escape(src)}" '
        'style="position:relative;padding-top:56.25%;overflow:hidden;">'
        f'<a href="{escape(url)}" rel="noopener nofollow" '
        'style="position:absolute;top:0;left:0;width:100%;height:100%;display:block;">'
        f'<img src="{escape(thumb)}" alt="{escape(thumb_alt)}" loading="lazy" decoding="async" '
        'referrerpolicy="no-referrer" style="width:100%;height:100%;object-fit:cover;">'
        '</a></div>'
    )
