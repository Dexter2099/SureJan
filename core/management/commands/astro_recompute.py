from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.cache import cache

from core.utils.astro import compute_astro_score


User = get_user_model()


class Command(BaseCommand):
    help = "Recompute AstroShield scores; cache astro_score:* and astro_band:* for 60 minutes."

    def handle(self, *args, **opts):
        n = 0
        qs = User.objects.filter(is_active=True).only("id", "date_joined")
        for user in qs.iterator():
            score, band = compute_astro_score(user)
            cache.set(f"astro_score:{user.id}", score, 3600)
            cache.set(f"astro_band:{user.id}", band, 3600)
            n += 1
        self.stdout.write(
            self.style.SUCCESS(f"AstroShield recompute complete ({n} users)")
        )
