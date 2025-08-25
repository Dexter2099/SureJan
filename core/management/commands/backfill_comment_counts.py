from django.core.management.base import BaseCommand
from django.db.models import Count

from core.models import Post, Comment


class Command(BaseCommand):
    help = "Recompute and store Post.comment_count from Comment table"

    def handle(self, *args, **options):
        qs = Post.objects.all().annotate(real_count=Count("comments"))
        updated = 0
        for p in qs:
            if p.comment_count != p.real_count:
                Post.objects.filter(pk=p.pk).update(comment_count=p.real_count)
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Updated {updated} posts"))

