from django import template

from ..utils.embed_builder import build_embed_iframe as _build_embed_iframe

register = template.Library()


@register.simple_tag
def build_embed_iframe(url):
    """Template tag wrapper for :func:`build_embed_iframe`."""
    return _build_embed_iframe(url)
