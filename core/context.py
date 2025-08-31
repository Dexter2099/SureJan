from django.conf import settings


def astro_constants(request):
    """Expose selected ASTRO* settings to templates."""
    return {
        "ASTROTURF_WATCH": settings.ASTROTURF_WATCH,
        "ASTRO_NEW_ACCOUNT_DAYS": settings.ASTRO_NEW_ACCOUNT_DAYS,
        "ASTRO_EARLY_VOTES_N": settings.ASTRO_EARLY_VOTES_N,
        "ASTRO_MIN_EARLY_VOTES": settings.ASTRO_MIN_EARLY_VOTES,
        "ASTRO_EARLY_SHARE_RED": settings.ASTRO_EARLY_SHARE_RED,
    }
