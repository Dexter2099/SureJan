from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Community

class Command(BaseCommand):
    help = "Seed initial communities"

    def handle(self, *args, **kwargs):
        seeds = [
            ("news", "News"),
            ("brisbane", "Brisbane"),
            ("tech", "Technology"),
            ("fun", "Fun"),
        ]
        U = get_user_model()
        user, _ = U.objects.get_or_create(username="admin")
        for slug, title in seeds:
            obj, created = Community.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": title,
                    "title": title,
                    "is_system": True,
                    "created_by": user,
                },
            )
            if not created and not obj.is_system:
                obj.is_system = True
                obj.save(update_fields=["is_system"])
            self.stdout.write(f"{'CREATED' if created else 'EXISTS '} r/{slug} (system)")
