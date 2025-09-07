from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q

from core.models import Post
from core.utils.thumbnails import cache_remote_image


class Command(BaseCommand):
    help = "Cache remote Rumble thumbnails and update posts to use local copies"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Do not save changes")

    def handle(self, *args, **opts):
        qs = (
            Post.objects.filter(post_type="link")
            .exclude(thumbnail_url__isnull=True)
            .exclude(thumbnail_url="")
            .filter(
                Q(thumbnail_url__icontains="rmbl.ws")
                | Q(thumbnail_url__icontains="rumblecdn.com")
            )
        )
        count = 0
        for p in qs.iterator():
            try:
                cached = cache_remote_image(p.thumbnail_url or "")
                if cached:
                    count += 1
                    if not opts["dry_run"]:
                        p.thumbnail_url = cached
                        p.save(update_fields=["thumbnail_url"])
                        connection.commit()
            except Exception as e:
                self.stderr.write(f"Post {p.id}: {e}")
        self.stdout.write(f"Converted {count} thumbnails")
