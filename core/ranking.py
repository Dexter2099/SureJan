from datetime import datetime, timezone
import math


def now():
    return datetime.now(timezone.utc)


def hours_since(dt):
    return max((now() - dt).total_seconds() / 3600, 1e-6)


def hot(score, created_at):
    age_h = max(hours_since(created_at), 0.5)
    return score / pow(age_h + 2.0, 1.8)


def rising(score, created_at):
    age_h = max(hours_since(created_at), 0.25)
    return score / age_h


def controversial(up, down):
    if up == 0 or down == 0:
        return 0.0
    total = up + down
    return total * min(up, down) / max(up, down)


def best(up, down, z=1.281551565545):  # 80% Wilson
    n = up + down
    if n == 0:
        return 0.0
    p = up / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (centre - margin) / denom


def recompute_post_ranks(post, up_count, down_count):
    score = post.score
    post.hot_rank = hot(score, post.created_at)
    post.rising_rank = rising(score, post.created_at)
    post.controversy = controversial(up_count, down_count)
    post.best_rank = best(up_count, down_count)
    post.save(update_fields=["hot_rank", "rising_rank", "controversy", "best_rank"])
    return post.hot_rank
