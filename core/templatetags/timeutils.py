from datetime import timedelta
from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def within_minutes(dt, minutes):
    if not dt:
        return False
    try:
        m = int(minutes)
    except (TypeError, ValueError):
        return False
    return (timezone.now() - dt) <= timedelta(minutes=m)
