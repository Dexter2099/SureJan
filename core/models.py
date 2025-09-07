from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password, check_password
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from datetime import timedelta
from django.utils import timezone
from django.utils.text import slugify, Truncator
from django.utils.html import strip_tags
from urllib.parse import urlparse
import logging
import re

from PIL import Image
from io import BytesIO
import os

from .ranking import recompute_post_ranks
from .utils.video_urls import canonicalize_video_url


MAX_BYTES = 4 * 1024 * 1024


def validate_image_file(f):
    if f.size > MAX_BYTES:
        raise forms.ValidationError("Image too large (max 4MB).")
    try:
        Image.open(f).verify()
    except Exception:
        raise forms.ValidationError("Upload must be an image.")
    finally:
        f.seek(0)


def _to_rgb(img):  # avoid RGBA in JPEG
    return img.convert("RGB") if img.mode not in ("L", "RGB") else img


def _reencode_jpeg(img: Image.Image, quality=85):
    buf = BytesIO()
    img = _to_rgb(img)
    # no 'exif' param => EXIF stripped
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return ContentFile(buf.getvalue())


def _resize_img(file, max_px=1600):
    file.seek(0)
    img = Image.open(file)
    img.thumbnail((max_px, max_px), Image.LANCZOS)
    new_file = _reencode_jpeg(img, quality=85)
    name, _ = os.path.splitext(getattr(file, "name", "image"))
    new_file.name = f"{name}.jpg"
    return new_file


def _make_thumb(file, max_px=400):
    file.seek(0)
    img = Image.open(file)
    img.thumbnail((max_px, max_px), Image.LANCZOS)
    new_file = _reencode_jpeg(img, quality=80)
    name, _ = os.path.splitext(getattr(file, "name", "thumb"))
    new_file.name = f"{name}_thumb.jpg"
    return new_file


class Community(models.Model):
    slug = models.SlugField(max_length=32, unique=True, db_index=True)
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


class Post(models.Model):
    community = models.ForeignKey(
        Community, on_delete=models.CASCADE, related_name="posts"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post_type = models.CharField(
        max_length=10,
        choices=[("text", "text"), ("link", "link"), ("image", "image")],
    )
    title = models.CharField(max_length=300)
    heading = models.CharField(max_length=500, blank=True)
    body = models.TextField(blank=True)
    content_url = models.URLField(blank=True)
    link_domain = models.CharField(max_length=120, blank=True)
    image = models.ImageField(
        upload_to="posts/", blank=True, null=True, validators=[validate_image_file]
    )
    image_thumb = models.ImageField(upload_to="posts/thumbs/", blank=True, null=True)
    score = models.IntegerField(default=0)
    hot_rank = models.FloatField(default=0, db_index=True)
    rising_rank = models.FloatField(default=0, db_index=True)
    controversy = models.FloatField(default=0, db_index=True)
    best_rank = models.FloatField(default=0, db_index=True)
    comment_count = models.IntegerField(default=0)
    is_draft = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    is_locked = models.BooleanField(default=False)
    slowmode = models.PositiveIntegerField(default=0)
    domain_weight = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def slug(self):
        return slugify(self.title)

    @property
    def excerpt(self):
        if self.body:
            text = strip_tags(self.body)
        elif self.link_domain:
            text = self.link_domain
        else:
            return ""
        text = re.sub(r"\s+", " ", text).strip()
        return Truncator(text).chars(180)

    @property
    def provider_name(self) -> str:
        """Return a human-friendly name for the linked content provider."""
        from .utils.providers import provider_from_domain

        return provider_from_domain(self.link_domain)

    def get_absolute_url(self):
        return reverse("post_detail", args=[self.community.slug, self.pk, self.slug])

    class Meta:
        indexes = [
            models.Index(fields=["community", "-created_at", "-id"]),
            models.Index(
                fields=["community", "-created_at"], name="post_comm_created_idx"
            ),
            models.Index(fields=["-hot_rank", "-created_at"]),
            models.Index(fields=["-score", "-created_at"]),
            models.Index(fields=["-controversy", "-created_at"]),
        ]

    def clean(self):
        super().clean()
        if (
            not self.is_deleted
            and self.post_type != "image"
            and not self.body
            and not self.content_url
        ):
            raise ValidationError("Either body or content_url is required.")

    def save(self, *args, **kwargs):
        recompute = kwargs.pop("recompute_hot", True)

        if self.content_url:
            canon_url = canonicalize_video_url(self.content_url)
            self.content_url = canon_url
            self.link_domain = urlparse(canon_url).netloc.lower().lstrip("www.")

        # Apply domain throttling weight on every save
        from .mod import domain_weight  # avoid circular import at module load

        if self.link_domain:
            self.domain_weight = domain_weight(self.link_domain)
        else:
            self.domain_weight = 1.0

        if self.image:
            resized = _resize_img(self.image)
            thumb = _make_thumb(resized)
            self.image.save(resized.name, resized, save=False)
            self.image_thumb.save(thumb.name, thumb, save=False)

        super().save(*args, **kwargs)
        if recompute and not kwargs.get("update_fields"):
            self.recompute_hot()

    def recompute_hot(self):
        up = Vote.objects.filter(target_type="post", target_id=self.pk, value=1).count()
        down = Vote.objects.filter(
            target_type="post", target_id=self.pk, value=-1
        ).count()
        return recompute_post_ranks(self, up, down)

    def can_author_delete(self, user, minutes=15):
        if user.is_staff:
            return True
        if user != self.author or self.is_deleted:
            return False
        return (timezone.now() - self.created_at) <= timedelta(minutes=minutes)

    def soft_delete(self, by_user):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = by_user
        self.title = "[deleted]"
        self.heading = ""
        self.body = ""
        self.content_url = ""
        self.link_domain = ""
        if self.image:
            self.image.delete(save=False)
            self.image = None
        if self.image_thumb:
            self.image_thumb.delete(save=False)
            self.image_thumb = None
        # Votes and anti-astroturf metrics are intentionally preserved; no
        # Vote rows are removed and aggregate metrics are left untouched.
        self.save(
            update_fields=[
                "is_deleted",
                "deleted_at",
                "deleted_by",
                "title",
                "heading",
                "body",
                "content_url",
                "link_domain",
                "image",
                "image_thumb",
            ],
            recompute_hot=False,
        )


class PostImageLink(models.Model):
    """External image URLs associated with a post (max five)."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="image_links")
    url = models.URLField()

    def save(self, *args, **kwargs):
        # Enforce a maximum of five images per post
        if not self.pk and self.post.image_links.count() >= 5:
            raise ValidationError("Maximum of 5 images per post")

        # Upgrade insecure HTTP URLs to HTTPS before saving
        if self.url and self.url.startswith("http://"):
            self.url = "https://" + self.url[len("http://") :]

        super().save(*args, **kwargs)


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
            models.Index(
                fields=["post", "-created_at"], name="comment_post_created_idx"
            ),
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


class Vote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target_type = models.CharField(
        max_length=10, choices=[("post", "post"), ("comment", "comment")]
    )
    target_id = models.PositiveBigIntegerField()
    value = models.SmallIntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(target_type__in=["post", "comment"]),
                name="vote_valid_target_type",
            ),
            models.UniqueConstraint(
                fields=["user", "target_type", "target_id"],
                name="uniq_vote_user_target",
            ),
        ]


class RecoveryCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recovery_codes",
    )
    code_hash = models.CharField(max_length=128)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    points_cached = models.IntegerField(default=0, db_index=True)
    is_banned = models.BooleanField(default=False)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


def get_points(user):
    if hasattr(user, "points_cached"):
        return user.points_cached
    return (
        getattr(user, "profile", None).points_cached if hasattr(user, "profile") else 0
    )


class RateLimitCounter(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rate_limits"
    )
    action = models.CharField(max_length=32)
    count = models.PositiveIntegerField(default=0)
    period_start = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "action")


class Report(models.Model):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey("content_type", "object_id")
    reason = models.TextField()
    is_note = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


class EngagementEvent(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="engagement_events"
    )
    event_type = models.CharField(max_length=32)
    voter_age_days = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["post", "-created_at"]),
            models.Index(fields=["created_at"]),
        ]


class PostBurstState(models.Model):
    post = models.OneToOneField(
        Post, on_delete=models.CASCADE, related_name="burst_state"
    )
    buckets = models.JSONField(default=list)
    bucket_index = models.PositiveSmallIntegerField(default=0)
    bucket_span_seconds = models.PositiveIntegerField(default=60)
    window_start = models.DateTimeField(default=timezone.now)
    total_5m = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)


class CommunityBaseline(models.Model):
    community = models.OneToOneField(
        Community, on_delete=models.CASCADE, related_name="baseline"
    )
    p95_votes_5m = models.FloatField(default=0)
    p95_votes_15m = models.FloatField(default=0)
    p10_comments_per_100_upvotes = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)


class AstroScore(models.Model):
    post = models.OneToOneField(
        Post, on_delete=models.CASCADE, related_name="astro_score"
    )
    community = models.ForeignKey(
        Community, on_delete=models.CASCADE, related_name="astro_scores"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="astro_scores"
    )
    rate5 = models.IntegerField(default=0)
    rate15 = models.IntegerField(default=0)
    early_new_share = models.FloatField(default=0)
    discuss_ratio = models.FloatField(default=0)
    score = models.IntegerField(default=1)
    severity = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class AstroUserSummary(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="astro_summary"
    )
    avg_score = models.FloatField(default=0)
    post_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)


class AstroCommunitySummary(models.Model):
    community = models.OneToOneField(
        Community, on_delete=models.CASCADE, related_name="astro_summary"
    )
    avg_score = models.FloatField(default=0)
    post_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)


# -- Vote side effects ------------------------------------------------------


@receiver(pre_save, sender=Vote)
def _store_old_vote_value(sender, instance, **kwargs):
    """Store the previous vote value on the instance before saving."""
    if instance.pk:
        instance._old_value = (
            Vote.objects.filter(pk=instance.pk).values_list("value", flat=True).first()
            or 0
        )
    else:
        instance._old_value = 0


def _apply_vote_delta(instance, delta):
    """Log vote deltas without mutating scores."""
    if delta == 0:
        return
    logging.getLogger(__name__).info(
        "Vote delta %s on %s %s by %s",
        delta,
        instance.target_type,
        instance.target_id,
        instance.user_id,
    )


@receiver(post_save, sender=Vote)
def _update_scores_on_vote_save(sender, instance, created, **kwargs):
    old = getattr(instance, "_old_value", 0)
    delta = instance.value - old
    _apply_vote_delta(instance, delta)


@receiver(post_delete, sender=Vote)
def _update_scores_on_vote_delete(sender, instance, **kwargs):
    _apply_vote_delta(instance, -instance.value)
