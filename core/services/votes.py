from django.db import transaction
from django.db.models import Sum

from ..models import Vote, Post, Comment


class AlreadyVoted(Exception):
    """Raised when a user attempts to vote more than once on a target."""



def _cast_vote_once(user, *, post=None, comment=None, want: int) -> int:
    """Internal helper to cast an immutable vote on a post or comment.

    Exactly one of ``post`` or ``comment`` must be provided. Returns the
    recomputed score for the target.
    """
    if want not in (1, -1):
        raise ValueError("Vote value must be +1 or -1")

    if (post is None) == (comment is None):
        raise ValueError("Specify exactly one of post or comment")

    target_type = "post" if post is not None else "comment"
    target_id = post.pk if post is not None else comment.pk
    target = post if post is not None else comment

    with transaction.atomic():
        row, _ = Vote.objects.select_for_update().get_or_create(
            user=user,
            target_type=target_type,
            target_id=target_id,
            defaults={"value": 0},
        )
        if row.value != 0:
            raise AlreadyVoted
        row.value = want
        row.save(update_fields=["value"])

        total = (
            Vote.objects.filter(target_type=target_type, target_id=target_id)
            .aggregate(t=Sum("value"))["t"]
            or 0
        )
        target.score = total
        target.save(update_fields=["score"])

    try:  # Anti-AstroTurf hook; non-blocking
        from core import anti_astroturf as aa

        aa.on_vote(user=user, target=target, value=want, immutable=True)
    except Exception:
        pass

    return total


def cast_vote_post_once(user, post: Post, want: int) -> int:
    """Cast an immutable vote on a post.

    Returns the post's new score or raises :class:`AlreadyVoted` if the user
    has already voted on the post.
    """
    return _cast_vote_once(user, post=post, want=want)


def cast_vote_comment_once(user, comment: Comment, want: int) -> int:
    """Cast an immutable vote on a comment.

    Returns the comment's new score or raises :class:`AlreadyVoted` if the user
    has already voted on the comment.
    """
    return _cast_vote_once(user, comment=comment, want=want)
