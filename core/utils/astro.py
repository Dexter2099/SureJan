from django.utils import timezone


def compute_astro_score(user) -> tuple[int, str]:
    """
    Return (score 0..100, band 'green'|'amber'|'red').
    Minimal heuristics, no DB writes.
    """
    now = timezone.now()
    age_days = (now - getattr(user, "date_joined", now)).days
    score = 0

    # Simple signals (replace/extend later without API change)
    if age_days < 3:  # very new account
        score += 25
    recent_vote_rate = getattr(user, "recent_vote_rate", 0)  # optional external calc
    if recent_vote_rate > 40:
        score += 40
    elif recent_vote_rate > 20:
        score += 25
    recent_posts = getattr(user, "recent_posts_count", 0)
    if recent_posts > 10:
        score += 20
    if getattr(user, "discuss_ratio_low", False):
        score += 10
    if getattr(user, "domain_repeat_high", False):
        score += 10

    score = max(0, min(100, score))
    band = "green" if score < 40 else ("amber" if score < 70 else "red")
    return score, band
