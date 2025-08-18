from datetime import datetime, timezone
from django.db import models

PAGE_SIZE = 15


def build_cursor(obj):
    return f"{int(obj.created_at.timestamp() * 1000)}.{obj.id}"


def parse_cursor(qs, cursor_str):
    if not cursor_str:
        return qs
    try:
        ts_ms, obj_id = cursor_str.split(".", 1)
        ts = datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc)
        obj_id = int(obj_id)
    except (ValueError, AttributeError):
        return qs
    return qs.filter(
        models.Q(created_at__lt=ts) | models.Q(created_at=ts, id__lt=obj_id)
    )
