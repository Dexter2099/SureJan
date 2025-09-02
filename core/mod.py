from datetime import timedelta
from django.core.cache import cache

THROTTLE_TTL = 7 * 24 * 60 * 60  # 7 days
KEY_PREFIX = "domain-throttle:"

def domain_weight(domain: str) -> float:
    """Return weight for a given domain (0.5 if throttled)."""
    if not domain:
        return 1.0
    return 0.5 if cache.get(f"{KEY_PREFIX}{domain.lower()}") else 1.0

def set_domain_throttle(domain: str, enabled: bool) -> None:
    """Toggle throttling for a domain and update existing posts."""
    domain = domain.lower()
    key = f"{KEY_PREFIX}{domain}"
    if enabled:
        cache.set(key, True, THROTTLE_TTL)
        from .models import Post
        Post.objects.filter(link_domain=domain).update(domain_weight=0.5)
    else:
        cache.delete(key)
        from .models import Post
        Post.objects.filter(link_domain=domain).update(domain_weight=1.0)

def remove_post(post, by_user):
    """Soft remove a post."""
    post.soft_delete(by_user)

def lock_post(post, locked: bool) -> None:
    """Lock or unlock a post's comments."""
    post.is_locked = locked
    post.save(update_fields=["is_locked"])
