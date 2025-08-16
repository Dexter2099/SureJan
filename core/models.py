from django.conf import settings
from django.db import models


class Community(models.Model):
    name = models.SlugField(max_length=32, unique=True, db_index=True)
    title = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"r/{self.name}"


class Post(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=10, choices=[("text", "text"), ("link", "link")])
    title = models.CharField(max_length=300)
    body = models.TextField(blank=True)
    url = models.URLField(blank=True)
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["community", "-created_at"])]
