from django.conf import settings
from django.db import models
from django.db.models.functions import Lower


class Community(models.Model):
    slug = models.SlugField(max_length=191, unique=True, db_index=True)
    name = models.CharField(max_length=80)
    title = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    wiki_html = models.TextField(blank=True, null=True)
    is_system = models.BooleanField(default=False, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="communities"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("name"), name="uniq_community_name_ci"),
        ]

    def __str__(self) -> str:
        return f"c/{self.slug}"


class CommunityBaseline(models.Model):
    community = models.OneToOneField(
        Community, on_delete=models.CASCADE, related_name="baseline"
    )
    p95_votes_5m = models.FloatField(default=0)
    p95_votes_15m = models.FloatField(default=0)
    p10_comments_per_100_upvotes = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)


class AstroCommunitySummary(models.Model):
    community = models.OneToOneField(
        Community, on_delete=models.CASCADE, related_name="astro_summary"
    )
    avg_score = models.FloatField(default=0)
    post_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

