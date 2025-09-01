from django import template
from django.conf import settings

register = template.Library()

@register.filter
def astro_band(score):
    """Return a band name for an AstroScore."""
    try:
        s = float(score)
    except (TypeError, ValueError):
        return ""
    if s >= settings.ASTRO_BAND_RED:
        return "red"
    if s >= settings.ASTRO_BAND_AMBER:
        return "amber"
    return "green"
