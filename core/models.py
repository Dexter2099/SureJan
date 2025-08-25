from django.conf import settings
from django.db import models
from django.db.models import F
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password, check_password
from django import forms
from django.core.files.base import ContentFile
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta
from django.utils import timezone

from PIL import Image
from io import BytesIO
import os

from .ranking import recompute_post_ranks


MAX_BYTES = 5 * 1024 * 1024


def validate_image_file(f):
    if f.size > MAX_BYTES:
        raise forms.ValidationError("Image too large (max 5MB).")
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
            models.UniqueConstraint(fields=["name"], name="uniq_community_name"),
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
    body = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    image = models.ImageField(
        upload_to="posts/", blank=True, null=True, validators=[validate_image_file]
    )
    image_thumb = models.ImageField(
        upload_to="posts/thumbs/", blank=True, null=True
    )
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
            models.Index(fields=["community", "-created_at"], name="post_comm_created_idx"),
            models.Index(fields=["-hot_rank", "-created_at"]),
            models.Index(fields=["-score", "-created_at"]),
            models.Index(fields=["-controversy", "-created_at"]),
        ]

    def save(self, *args, **kwargs):
        recompute = kwargs.pop("recompute_hot", True)

        if self.image:
            resized = _resize_img(self.image)
            thumb = _make_thumb(resized)
            self.image.save(resized.name, resized, save=False)
            self.image_thumb.save(thumb.name, thumb, save=False)

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

    def can_author_delete(self, user, minutes=15):
        """Return whether a user may delete this post."""
        if not getattr(user, "is_authenticated", False):
            return False
        if user.is_staff:
            return True
        if user != self.author:
            return False
        return timezone.now() - self.created_at <= timedelta(minutes=minutes)

    def soft_delete(self, user):
        """Soft delete the post, keeping a tombstone record."""
        self.title = "[deleted]"
        self.body = ""
        self.url = ""
        if self.image:
            self.image.delete(save=False)
            self.image = None
        if self.image_thumb:
            self.image_thumb.delete(save=False)
            self.image_thumb = None
        self.save(update_fields=["title", "body", "url", "image", "image_thumb"])


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
        indexes = [
            models.Index(fields=["post", "path"]),
            models.Index(fields=["post", "-created_at"], name="comment_post_created_idx"),
        ]

    @property
    def depth(self):
        """Return the nesting depth based on the comment path."""
        return self.path.count("/")


class Vote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target_type = models.CharField(
        max_length=10, choices=[("post", "post"), ("comment", "comment")]
    )
    target_id = models.PositiveBigIntegerField()
    value = models.SmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "target_type", "target_id"],
                name="uniq_vote_target_user",
            )
        ]


class RecoveryCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recovery_codes"
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
    return getattr(user, "profile", None).points_cached if hasattr(user, "profile") else 0


class Report(models.Model):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey("content_type", "object_id")
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


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
    """Apply the vote delta to the target object and author points."""
    if delta == 0:
        return
    if instance.target_type == "post":
        Post.objects.filter(pk=instance.target_id).update(score=F("score") + delta)
        post = Post.objects.get(pk=instance.target_id)
        # recompute ranking based on current vote counts
        up = Vote.objects.filter(
            target_type="post", target_id=instance.target_id, value=1
        ).count()
        down = Vote.objects.filter(
            target_type="post", target_id=instance.target_id, value=-1
        ).count()
        recompute_post_ranks(post, up, down)
        UserProfile.objects.filter(user=post.author_id).update(
            points_cached=F("points_cached") + delta
        )
    else:
        Comment.objects.filter(pk=instance.target_id).update(score=F("score") + delta)
        comment = Comment.objects.get(pk=instance.target_id)
        UserProfile.objects.filter(user=comment.author_id).update(
            points_cached=F("points_cached") + delta
        )


@receiver(post_save, sender=Vote)
def _update_scores_on_vote_save(sender, instance, created, **kwargs):
    old = getattr(instance, "_old_value", 0)
    delta = instance.value - old
    _apply_vote_delta(instance, delta)


@receiver(post_delete, sender=Vote)
def _update_scores_on_vote_delete(sender, instance, **kwargs):
    _apply_vote_delta(instance, -instance.value)


# Re-export apply_vote for backwards compatibility
from .votes import apply_vote  # noqa: E402
