from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0020_embed_astroscore_post_embed_postimagelink_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="astroscore",
            name="score",
            field=models.IntegerField(default=1),
        ),
        migrations.CreateModel(
            name="AstroUserSummary",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("avg_score", models.FloatField(default=0)),
                ("post_count", models.IntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="astro_summary",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AstroCommunitySummary",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("avg_score", models.FloatField(default=0)),
                ("post_count", models.IntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "community",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="astro_summary",
                        to="core.community",
                    ),
                ),
            ],
        ),
    ]
