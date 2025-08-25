from django.core.management.base import BaseCommand
from django.db.models import Q

from core.models import Post, _make_thumb


class Command(BaseCommand):
    help = "Generate thumbnails for posts that have an image but no image_thumb"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=500)

    def handle(self, *args, **opts):
        qs = (
            Post.objects.filter(image__isnull=False)
            .filter(Q(image_thumb="") | Q(image_thumb__isnull=True))
        )
        count = 0
        for p in qs.iterator():
            try:
                p.image.open()
                thumb = _make_thumb(p.image)
                p.image_thumb.save(thumb.name, thumb, save=False)
                p.save(update_fields=["image_thumb"])
                count += 1
                if count >= opts["limit"]:
                    break
            except Exception as e:
                self.stderr.write(f"Post {p.id}: {e}")
        self.stdout.write(f"Backfilled {count} thumbnails")
