from django.conf import settings
from django.db import models
import math
from django.utils import timezone


class Community(models.Model):
    name = models.SlugField(max_length=32, unique=True, db_index=True)
    title = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"c/{self.name}"


class Post(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=10, choices=[("text", "text"), ("link", "link")])
    title = models.CharField(max_length=300)
    body = models.TextField(blank=True)
    url = models.URLField(blank=True)
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    hot_rank = models.FloatField(default=0, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["community", "-created_at"])]

    def save(self, *args, **kwargs):
        recompute = kwargs.pop("recompute_hot", True)
        super().save(*args, **kwargs)
        if recompute and not kwargs.get("update_fields"):
            self.recompute_hot()

    def recompute_hot(self):
        now = timezone.now()
        age_hours = max((now - self.created_at).total_seconds() / 3600, 0.5)
        hot = self.score / math.pow(age_hours + 2, 1.8)
        self.hot_rank = hot
        Post = self.__class__
        Post.objects.filter(pk=self.pk).update(hot_rank=hot)
        return hot


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Vote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target_type = models.CharField(
        max_length=10, choices=[("post", "post"), ("comment", "comment")]
    )
    target_id = models.PositiveIntegerField()
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
        target.recompute_hot()
    return target.score
