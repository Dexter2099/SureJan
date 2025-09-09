from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_delete_vote"),
    ]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="image",
            field=models.ImageField(
                upload_to="posts/", blank=True, null=True, max_length=255
            ),
        ),
    ]

