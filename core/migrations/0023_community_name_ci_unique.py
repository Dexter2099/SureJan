from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0022_post_moderation_fields"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="community",
            name="uniq_community_name",
        ),
        migrations.AddConstraint(
            model_name="community",
            constraint=models.UniqueConstraint(
                Lower("name"),
                name="uniq_community_name_ci",
            ),
        ),
    ]
