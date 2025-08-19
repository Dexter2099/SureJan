from django import template
from core.models import get_points as _get_points

register = template.Library()


@register.filter
def get_points(user):
    return _get_points(user)
