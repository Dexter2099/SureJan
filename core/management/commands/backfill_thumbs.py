import asyncio

from django.core.cache import cache
from django.core.management.base import BaseCommand
from asgiref.sync import sync_to_async
from django.db import connection
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

from core import og_fetch_config
from core.models import Post, _make_thumb
from core.utils.thumbnails import resolve_thumbnail, persist_thumbnail
from core.utils.url_cleanup import cleanup_url


class Command(BaseCommand):
    help = (
        "Generate thumbnails for posts that have an image but no image_thumb "
        "and link posts missing an image"
    )

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=500)
        parser.add_argument("--days", type=int, default=7, help="Only process posts newer than this many days")
        parser.add_argument(
            "--timeout",
            type=float,
            default=2.0,
            help="HTTP timeout for remote thumbnail fetches (seconds)",
        )
        parser.add_argument(
            "--concurrency",
            type=int,
            default=10,
            help="Number of concurrent thumbnail fetches",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch thumbnails without saving changes",
        )

    def handle(self, *args, **opts):
        qs_img = (
            Post.objects.filter(image__isnull=False)
            .exclude(image="")
            .filter(Q(image_thumb="") | Q(image_thumb__isnull=True))
        )
        cutoff = timezone.now() - timedelta(days=opts["days"])
        qs_link = (
            Post.objects.filter(post_type="link", created_at__gte=cutoff)
            .filter(Q(image="") | Q(image__isnull=True))
            .exclude(content_url="")
            .order_by("-created_at")
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
            limit = opts["limit"] - count
            posts = list(qs_link[:limit])
            og_fetch_config.CONNECT_TIMEOUT = opts["timeout"]
            og_fetch_config.READ_TIMEOUT = opts["timeout"]

            if connection.vendor == "sqlite":
                def worker_sync(post):
                    try:
                        fail_key = f"thumbfail:{cleanup_url(post.content_url or '')}"
                        if cache.get(fail_key):
                            return 0
                        src, _ = resolve_thumbnail(
                            post.content_url or "",
                            post.title,
                            True,
                        )
                        if src and src.startswith("https://"):
                            persist_thumbnail(post, src, post.title)
                            return 1 if post.image else 0
                        elif src and src.startswith(settings.MEDIA_URL):
                            post.image = src[len(settings.MEDIA_URL) :]
                            Post.objects.filter(pk=post.pk).update(image=post.image)
                            return 1
                        return 0
                    except Exception as e:
                        self.stderr.write(f"Post {post.id}: {e}")
                        return 0

                count += sum(worker_sync(p) for p in posts)
            else:
                async def worker(post):
                    try:
                        fail_key = f"thumbfail:{cleanup_url(post.content_url or '')}"
                        if cache.get(fail_key):
                            return 0
                        src, _ = await asyncio.to_thread(
                            resolve_thumbnail,
                            post.content_url or "",
                            post.title,
                            True,
                        )
                        if src and src.startswith("https://"):
                            await asyncio.to_thread(
                                persist_thumbnail, post, src, post.title
                            )
                            return 1 if post.image else 0
                        elif src and src.startswith(settings.MEDIA_URL):
                            post.image = src[len(settings.MEDIA_URL) :]
                            await sync_to_async(
                                Post.objects.filter(pk=post.pk).update,
                                thread_sensitive=True,
                            )(image=post.image)
                            return 1
                        return 0
                    except Exception as e:
                        self.stderr.write(f"Post {post.id}: {e}")
                        return 0

                async def runner():
                    sem = asyncio.Semaphore(opts["concurrency"])

                    async def run(post):
                        async with sem:
                            return await worker(post)

                    return sum(await asyncio.gather(*(run(p) for p in posts)))

                count += asyncio.run(runner())
        self.stdout.write(f"Backfilled {count} thumbnails")
