from datetime import timedelta

from django.utils import timezone
from django.db.models import F

from ..models import Post

TAB_ORDER = {
    "hot": ["-weighted_hot", "-created_at", "-id"],
    "new": ["-created_at", "-id"],
    "top": ["-weighted_score", "-created_at", "-id"],
}

RANGE_MAP = {
    "24h": timedelta(days=1),
    "7d": timedelta(days=7),
}


def feed_queryset(tab: str, t: str, base_qs=None):
    """Return a queryset for the given tab and time range."""
    order = TAB_ORDER.get(tab, TAB_ORDER["hot"])
    qs = (
        base_qs
        if base_qs is not None
        else Post.objects.select_related("community", "author")
    )
    qs = qs.filter(is_deleted=False).annotate(
        weighted_hot=F("hot_rank") * F("domain_weight"),
        weighted_score=F("score") * F("domain_weight"),
    ).order_by(*order)
    if tab == "top" and t and t != "all":
        delta = RANGE_MAP.get(t)
        if delta:
            since = timezone.now() - delta
            qs = qs.filter(created_at__gte=since)
    return qs
