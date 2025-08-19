from django.conf import settings
from django.db import models
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver

from .ranking import recompute_post_ranks


class Community(models.Model):
    slug = models.SlugField(max_length=32, unique=True, db_index=True)
    name = models.CharField(max_length=80)
    title = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="communities"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"c/{self.slug}"


class Post(models.Model):
    community = models.ForeignKey(
        Community, on_delete=models.CASCADE, related_name="posts"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=10, choices=[("text", "text"), ("link", "link")])
    title = models.CharField(max_length=300)
    body = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    score = models.IntegerField(default=0)
    hot_rank = models.FloatField(default=0, db_index=True)
    rising_rank = models.FloatField(default=0, db_index=True)
    controversy = models.FloatField(default=0, db_index=True)
    best_rank = models.FloatField(default=0, db_index=True)
    comment_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["community", "-created_at", "-id"]),
            models.Index(fields=["-hot_rank", "-created_at"]),
            models.Index(fields=["-score", "-created_at"]),
            models.Index(fields=["-controversy", "-created_at"]),
        ]

    def save(self, *args, **kwargs):
        recompute = kwargs.pop("recompute_hot", True)
        super().save(*args, **kwargs)
        if recompute and not kwargs.get("update_fields"):
            self.recompute_hot()

    def recompute_hot(self):
        up = Vote.objects.filter(
            target_type="post", target_id=self.pk, value=1
        ).count()
        down = Vote.objects.filter(
            target_type="post", target_id=self.pk, value=-1
        ).count()
        return recompute_post_ranks(self, up, down)


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

    class Meta:
        indexes = [models.Index(fields=["post", "path"])]

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            if self.parent:
                self.path = f"{self.parent.path}/{self.pk:04d}"
            else:
                self.path = f"{self.pk:04d}"
            Comment.objects.filter(pk=self.pk).update(path=self.path)
            Post.objects.filter(pk=self.post_id).update(
                comment_count=F("comment_count") + 1
            )


class Vote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target_type = models.CharField(
        max_length=10, choices=[("post", "post"), ("comment", "comment")]
    )
    target_id = models.PositiveBigIntegerField()
    value = models.SmallIntegerField()

    class Meta:
        unique_together = ("user", "target_type", "target_id")


def apply_vote(user, target_type, target_id, value):
    """Apply a vote to a post or comment and return the new score."""
    if value not in (-1, 1):
        raise ValueError("Invalid vote value")

    if target_type == "post":
        model = Post
    elif target_type == "comment":
        model = Comment
    else:
        raise ValueError("Invalid target type")

    target = model.objects.get(pk=target_id)
    vote, created = Vote.objects.get_or_create(
        user=user,
        target_type=target_type,
        target_id=target_id,
        defaults={"value": value},
    )

    if created:
        target.score += value
    else:
        if vote.value == value:
            target.score -= value
            vote.delete()
        else:
            delta = value - vote.value
            vote.value = value
            vote.save(update_fields=["value"])
            target.score += delta

    target.save(update_fields=["score"])
    if target_type == "post":
        up = Vote.objects.filter(
            target_type="post", target_id=target_id, value=1
        ).count()
        down = Vote.objects.filter(
            target_type="post", target_id=target_id, value=-1
        ).count()
        recompute_post_ranks(target, up, down)
    return target.score


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    points_cached = models.IntegerField(default=0, db_index=True)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


def get_points(user):
    if hasattr(user, "points_cached"):
        return user.points_cached
    return getattr(user, "profile", None).points_cached if hasattr(user, "profile") else 0
