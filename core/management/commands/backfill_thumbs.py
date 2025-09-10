from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image

from core.models import Post
from django.db.models import Q


class Command(BaseCommand):
    help = "Generate thumbnails for posts missing image_thumb"

    def handle(self, *args, **options):
        qs = Post.objects.filter(image__isnull=False).filter(
            Q(image_thumb="") | Q(image_thumb__isnull=True)
        )
        count = qs.count()
        self.stdout.write(f"Found {count} posts needing thumbnails...")

        done = 0
        for post in qs.iterator():
            try:
                post.image.open()
                img = Image.open(post.image).convert("RGB")

                # Resize if wider than 480px
                w, h = img.size
                max_w = 480
                if w > max_w:
                    new_h = int(h * (max_w / float(w)))
                    img = img.resize((max_w, new_h), Image.LANCZOS)

                buf = BytesIO()
                img.save(buf, format="JPEG", quality=80, optimize=True)
                thumb_file = ContentFile(buf.getvalue())

                base = post.image.name.rsplit("/", 1)[-1].rsplit(".", 1)[0]
                post.image_thumb.save(f"thumb_{base}.jpg", thumb_file, save=False)
                post.save(update_fields=["image_thumb"])
                done += 1
            except Exception as e:
                self.stderr.write(f"Failed on post {post.pk}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Backfill complete: {done} thumbnails created"))

