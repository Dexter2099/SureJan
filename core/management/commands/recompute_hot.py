from django.core.management.base import BaseCommand
from core.models import Post


class Command(BaseCommand):
    help = "Recompute hot ranking for all posts"

    def handle(self, *args, **options):
        for post in Post.objects.all():
            post.recompute_hot()
        self.stdout.write("recomputed")
