from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


def cleanup_votes(apps, schema_editor):
    """Remove votes without a clear post or comment target."""

    Vote = apps.get_model("core", "Vote")
    Vote.objects.filter(
        Q(target_type__isnull=True)
        | ~Q(target_type__in=["post", "comment"])
        | Q(target_id__isnull=True)
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_community_name_ci_unique"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(cleanup_votes, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="vote",
            name="uniq_vote_target_user",
        ),
        migrations.AddConstraint(
            model_name="vote",
            constraint=models.CheckConstraint(
                check=Q(target_type__in=["post", "comment"]),
                name="vote_valid_target_type",
            ),
        ),
        migrations.AddConstraint(
            model_name="vote",
            constraint=models.UniqueConstraint(
                fields=["user", "target_id"],
                condition=Q(target_type="post"),
                name="uniq_vote_post_user",
            ),
        ),
        migrations.AddConstraint(
            model_name="vote",
            constraint=models.UniqueConstraint(
                fields=["user", "target_id"],
                condition=Q(target_type="comment"),
                name="uniq_vote_comment_user",
            ),
        ),
    ]

