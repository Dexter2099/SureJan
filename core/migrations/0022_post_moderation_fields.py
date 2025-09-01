from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0021_astroscore_score_and_summaries"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="is_locked",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="post",
            name="slowmode",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="post",
            name="domain_weight",
            field=models.FloatField(default=1.0),
        ),
        migrations.AddField(
            model_name="report",
            name="is_note",
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
