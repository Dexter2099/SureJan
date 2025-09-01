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
    "day": timedelta(days=1),
    "7days": timedelta(days=7),
    "month": timedelta(days=30),
    "year": timedelta(days=365),
}


def feed_queryset(tab: str, range_: str):
    """Return a queryset for the given tab and time range."""
    order = TAB_ORDER.get(tab, TAB_ORDER["hot"])
    qs = Post.objects.select_related("community", "author").order_by(*order)
    if range_ != "all":
        delta = RANGE_MAP.get(range_)
        if delta:
            since = timezone.now() - delta
            qs = qs.filter(created_at__gte=since)
    return qs
