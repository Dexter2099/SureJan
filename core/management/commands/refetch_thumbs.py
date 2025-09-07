from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import Post
from core.utils.thumbnails import resolve_thumbnail


class Command(BaseCommand):
    help = "Re-fetch thumbnails for posts with off-site thumbnail URLs"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100, help="Maximum posts to process")

    def handle(self, *args, **opts):
        qs = (
            Post.objects.filter(post_type="link")
            .exclude(thumbnail_url__isnull=True)
            .exclude(thumbnail_url="")
            .exclude(thumbnail_url__startswith=settings.MEDIA_URL)
            .exclude(thumbnail_url__startswith="data:")
            .order_by("-created_at")[: opts["limit"]]
        )
        count = 0
        for post in qs:
            try:
                src, alt = resolve_thumbnail(
                    post.content_url or "", post.title, fetch_remote=True
                )
                if src and src.startswith(settings.MEDIA_URL):
                    post.thumbnail_url = src
                    post.thumbnail_alt = alt
                    post.save(update_fields=["thumbnail_url", "thumbnail_alt"])
                    count += 1
            except Exception as e:  # pragma: no cover - log and continue
                self.stderr.write(f"Post {post.id}: {e}")
        self.stdout.write(f"Refetched {count} thumbnails")
