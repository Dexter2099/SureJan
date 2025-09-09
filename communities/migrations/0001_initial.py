from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.functions.text


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Community",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("slug", models.SlugField(max_length=191, unique=True)),
                ("name", models.CharField(max_length=80)),
                ("title", models.CharField(max_length=80)),
                ("description", models.TextField(blank=True)),
                ("wiki_html", models.TextField(blank=True, null=True)),
                ("is_system", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="communities",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        django.db.models.functions.text.Lower("name"),
                        name="uniq_community_name_ci",
                    )
                ]
            },
        ),
        migrations.CreateModel(
            name="AstroCommunitySummary",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("avg_score", models.FloatField(default=0)),
                ("post_count", models.IntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "community",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="astro_summary",
                        to="communities.community",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CommunityBaseline",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("p95_votes_5m", models.FloatField(default=0)),
                ("p95_votes_15m", models.FloatField(default=0)),
                ("p10_comments_per_100_upvotes", models.FloatField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "community",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="baseline",
                        to="communities.community",
                    ),
                ),
            ],
        ),
    ]

