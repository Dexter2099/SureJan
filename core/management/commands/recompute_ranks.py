"""Recompute post rank metrics from vote counts.

Usage:
    python manage.py recompute_ranks
"""

from django.core.management.base import BaseCommand

from core.models import Post
from votes.models import Vote
from core.ranking import recompute_post_ranks


class Command(BaseCommand):
    """Recompute ranking metrics for all posts."""

    help = "Recompute rank metrics for all posts."

    def handle(self, *args, **options):
        for post in Post.objects.all():
            up = Vote.objects.filter(
                target_type="post", target_id=post.pk, value=1
            ).count()
            down = Vote.objects.filter(
                target_type="post", target_id=post.pk, value=-1
            ).count()
            recompute_post_ranks(post, up, down)
        self.stdout.write(self.style.SUCCESS("recomputed"))

