from django import template
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
