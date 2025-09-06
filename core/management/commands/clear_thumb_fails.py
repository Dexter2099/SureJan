from django.core.management.base import BaseCommand
from django.core.cache import cache

from core.models import Post


class Command(BaseCommand):
    help = "Clear SVG thumbnail placeholders and thumbnail failure cache keys"

    def handle(self, *args, **opts):
        qs = Post.objects.filter(thumbnail_url__startswith="data:image/svg+xml")
        count = qs.count()
        qs.update(thumbnail_url="", thumbnail_alt="")
        self.stdout.write(f"Cleared {count} placeholder thumbnails")

        deleted = 0
        if hasattr(cache, "delete_pattern"):
            cache.delete_pattern("thumbfail:*")
        else:
            try:
                for key in list(getattr(cache, "_cache", {}).keys()):
                    if str(key).startswith("thumbfail:"):
                        cache.delete(key)
                        deleted += 1
            except Exception:
                pass
        if deleted:
            self.stdout.write(f"Deleted {deleted} thumbfail cache keys")
