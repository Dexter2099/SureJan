from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q

from core.models import Post
from core.utils.thumbnails import resolve_thumbnail, persist_thumbnail


class Command(BaseCommand):
    help = "Re-fetch thumbnails for posts missing images"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100, help="Maximum posts to process")

    def handle(self, *args, **opts):
        qs = (
            Post.objects.filter(post_type="link")
            .filter(Q(image="") | Q(image__isnull=True))
            .exclude(content_url="")
            .order_by("-created_at")[: opts["limit"]]
        )
        count = 0
        for post in qs:
            try:
                src, _ = resolve_thumbnail(
                    post.content_url or "", post.title, fetch_remote=True
                )
                if src and src.startswith("https://"):
                    persist_thumbnail(post, src, post.title)
                elif src and src.startswith(settings.MEDIA_URL):
                    post.image = src[len(settings.MEDIA_URL) :]
                    Post.objects.filter(pk=post.pk).update(image=post.image)
                if post.image:
                    count += 1
            except Exception as e:  # pragma: no cover - log and continue
                self.stderr.write(f"Post {post.id}: {e}")
        self.stdout.write(f"Refetched {count} thumbnails")

