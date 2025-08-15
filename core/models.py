from django.conf import settings
from django.db import models


class Community(models.Model):
    """A group for users with a shared interest."""

    name = models.SlugField(max_length=32, unique=True, db_index=True)
    title = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.title


class Subscription(models.Model):
    """A membership linking a user to a community."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "community")


class Media(models.Model):
    """Uploaded media associated with posts."""

    KIND_CHOICES = [
        ("image", "Image"),
        ("video", "Video"),
    ]

    kind = models.CharField(max_length=5, choices=KIND_CHOICES)
    file = models.FileField(upload_to="media/%Y/%m/%d/")
    thumb = models.ImageField(
        upload_to="thumbs/%Y/%m/%d/", null=True, blank=True
    )
    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Post(models.Model):
    """A submission to a community."""

    POST_TYPES = [
        ("text", "Text"),
        ("link", "Link"),
        ("image", "Image"),
    ]

    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=5, choices=POST_TYPES)
    title = models.CharField(max_length=300)
    body = models.TextField(blank=True)
    url = models.URLField(blank=True)
    media = models.ForeignKey(Media, null=True, blank=True, on_delete=models.SET_NULL)
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["community", "-created_at"])]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.title


class Comment(models.Model):
    """A comment on a post."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True
    )
    body = models.TextField()
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Vote(models.Model):
    """A user's vote on a post or comment."""

    TARGET_CHOICES = [
        ("post", "Post"),
        ("comment", "Comment"),
    ]
    VALUE_CHOICES = [(-1, "Downvote"), (1, "Upvote")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target_type = models.CharField(max_length=7, choices=TARGET_CHOICES)
    target_id = models.IntegerField()
    value = models.SmallIntegerField(choices=VALUE_CHOICES)

    class Meta:
        unique_together = ("user", "target_type", "target_id")

