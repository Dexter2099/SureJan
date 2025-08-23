from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import Community

COMMUNITIES = [
    ("news", "News"),
    ("brisbane", "Brisbane"),
]


class Command(BaseCommand):
    help = "Seed basic communities"

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.first()
        if not user:
            user = User.objects.create_user("admin")
        for slug, name in COMMUNITIES:
            community, created = Community.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "title": name,
                    "created_by": user,
                },
            )
            if created:
                self.stdout.write(f"CREATED {slug}")
            else:
                self.stdout.write(f"EXISTS {slug}")
