from django.utils import timezone

from core.models import Post
from .models import Comment


def create_comment(*, post: Post, author, body: str, parent: Comment | None = None) -> Comment:
    if parent:
        child_seq = parent.children.count() + 1
        path = f"{parent.path}/{child_seq:04d}"
    else:
        root_seq = post.comments.filter(parent__isnull=True).count() + 1
        path = f"{root_seq:04d}"
    comment = Comment.objects.create(
        post=post,
        author=author,
        parent=parent,
        body=body,
        path=path,
    )
    return comment


def edit_comment(comment: Comment, body: str) -> Comment:
    comment.body = body
    comment.edited_at = timezone.now()
    comment.save(update_fields=["body", "edited_at"])
    return comment


def delete_comment(comment: Comment, by_user) -> Comment:
    comment.soft_delete(by_user)
    return comment
