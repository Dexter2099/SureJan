from django.conf import settings
from django.db import models
from django.db.models import Q


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
