from django.core.management.base import BaseCommand
from django.db.models import Q

from core.models import Post, _make_thumb
from core.utils.thumbnails import resolve_thumbnail


class Command(BaseCommand):
    help = (
        "Generate thumbnails for posts that have an image but no image_thumb "
        "and link posts missing thumbnail_url"
    )

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=500)

    def handle(self, *args, **opts):
        qs_img = (
            Post.objects.filter(image__isnull=False)
            .filter(Q(image_thumb="") | Q(image_thumb__isnull=True))
        )
        qs_link = (
            Post.objects.filter(post_type="link")
            .filter(Q(thumbnail_url="") | Q(thumbnail_url__isnull=True))
            .exclude(content_url="")
        )
        count = 0
        for p in qs_img.iterator():
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
        if count < opts["limit"]:
            for p in qs_link.iterator():
                try:
                    src, alt = resolve_thumbnail(
                        p.content_url or "", p.title, fetch_remote=True
                    )
                    p.thumbnail_url = src
                    p.thumbnail_alt = alt
                    p.save(update_fields=["thumbnail_url", "thumbnail_alt"])
                    count += 1
                    if count >= opts["limit"]:
                        break
                except Exception as e:
                    self.stderr.write(f"Post {p.id}: {e}")
        self.stdout.write(f"Backfilled {count} thumbnails")
