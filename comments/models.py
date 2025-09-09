from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import Post


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    path = models.TextField(db_index=True, blank=True, default="")
    body = models.TextField()
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        indexes = [
            models.Index(fields=["post", "path"]),
            models.Index(fields=["post", "-created_at"], name="comment_post_created_idx"),
        ]

    @property
    def depth(self):
        """Return the nesting depth based on the comment path."""
        return self.path.count("/")

    def soft_delete(self, by_user):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = by_user
        self.body = ""
        # Votes and AA metrics remain unchanged; we keep vote records and do not
        # recompute any aggregate analytics.
        # Saving with update_fields ensures post_save signals detect the deletion.
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "body"])
