from django.conf import settings
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
            .exclude(image__isnull=True)
            .exclude(image="")
            .filter(
                Q(image__icontains="rmbl.ws") | Q(image__icontains="rumblecdn.com")
            )
        )
        count = 0
        for p in qs.iterator():
            try:
                cached = cache_remote_image(p.image.name if p.image else "")
                if cached:
                    count += 1
                    if not opts["dry_run"]:
                        rel = (
                            cached[len(settings.MEDIA_URL) :]
                            if cached.startswith(settings.MEDIA_URL)
                            else cached
                        )
                        Post.objects.filter(pk=p.pk).update(image=rel)
                        connection.commit()
            except Exception as e:
                self.stderr.write(f"Post {p.id}: {e}")
        self.stdout.write(f"Converted {count} thumbnails")
