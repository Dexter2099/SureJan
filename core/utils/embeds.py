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
    # Prefer secure thumbnails when available
    if thumb.startswith("http://"):
        thumb = "https://" + thumb[len("http://") :]
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

        # 3) Thumbnail fallback: when oEmbed misses it, use a tiny inline SVG
        #    (keeps CSP-friendly, no external host needed)
        if not thumb:
            svg = (
                "data:image/svg+xml;utf8,"
                "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 675'>"
                "<rect width='1200' height='675' fill='%23e5e5e5'/>"
                "<circle cx='600' cy='337' r='120' fill='%23999'/>"
                "<polygon points='560,277 560,397 660,337' fill='white'/>"
                "<text x='50%' y='90%' dominant-baseline='middle' text-anchor='middle' "
                "font-family='system-ui, sans-serif' font-size='40' fill='%23666'>Rumble preview</text>"
                "</svg>"
            )
            thumb = svg

        return (
            f'<div class="post-embed" data-src="{escape(src)}" '
            f'style="position:relative;padding-top:56.25%;overflow:hidden;">'
            f'  <a href="{escape(url)}" rel="noopener nofollow" '
            f'style="position:absolute;top:0;left:0;width:100%;height:100%;display:block;">'
            f'    <img src="{escape(thumb)}" alt="" loading="lazy" decoding="async" '
            f'referrerpolicy="no-referrer" style="width:100%;height:100%;object-fit:cover;">'
            f'  </a>'
            f'</div>'
        )
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
