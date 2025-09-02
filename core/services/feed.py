from datetime import timedelta

from django.utils import timezone

from ..models import Post

TAB_ORDER = {
    "hot": ["-hot_rank", "-created_at", "-id"],
    "new": ["-created_at", "-id"],
    "rising": ["-rising_rank", "-created_at", "-id"],
    "controversial": ["-controversy", "-created_at", "-id"],
    "top": ["-score", "-created_at", "-id"],
}

RANGE_MAP = {
    "24h": timedelta(days=1),
    "7d": timedelta(days=7),
}


def feed_queryset(tab: str, t: str):
    """Return a queryset for the given tab and time range."""
    order = TAB_ORDER.get(tab, TAB_ORDER["hot"])
    qs = Post.objects.select_related("community", "author").order_by(*order)
    if t and t != "all":
        delta = RANGE_MAP.get(t)
        if delta:
            since = timezone.now() - delta
            qs = qs.filter(created_at__gte=since)
    return qs
