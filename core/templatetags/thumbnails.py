from django import template
from django.conf import settings

from ..utils.thumbnails import svg_placeholder as _svg_placeholder

register = template.Library()

@register.simple_tag
def svg_placeholder(label, alt=None):
    """Return SVG placeholder data for templates.

    Returns a dict with ``src`` and ``alt`` keys suitable for use with
    ``as`` in templates.
    """
    src, alt_text = _svg_placeholder(label, alt)
    return {"src": src, "alt": alt_text}


@register.filter
def local_thumb(url: str) -> str:
    """Return ``url`` if it is under ``MEDIA_URL``.

    Any URL not starting with ``MEDIA_URL`` is treated as missing so templates
    can fall back to placeholders instead of rendering remote thumbnails.
    """
    if url and url.startswith(settings.MEDIA_URL):
        return url
    return ""
