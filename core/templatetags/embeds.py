from django import template
from core.utils.embeds import build_embed_html as _build_embed_html

register = template.Library()


@register.filter
def build_embed_html(url: str) -> str:
    """Return embed HTML or a link card for ``url``."""
    return _build_embed_html(url)
