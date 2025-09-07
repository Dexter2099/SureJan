from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clear thumbnail failure cache keys"

    def handle(self, *args, **opts):
        if hasattr(cache, "delete_pattern"):
            cache.delete_pattern("thumbfail:*")
        else:
            cache.clear()
        self.stdout.write("Cleared thumbnail failure cache")

