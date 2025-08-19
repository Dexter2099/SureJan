from urllib.parse import urlparse
from django import template

register = template.Library()


@register.filter
def domain(url: str) -> str:
    """Return the domain/host for a URL."""
    if not url:
        return ""
    return urlparse(url).netloc
