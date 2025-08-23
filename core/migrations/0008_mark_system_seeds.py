from django.db import migrations


def mark_system(apps, schema_editor):
    Community = apps.get_model("core", "Community")
    for slug in ["news", "brisbane"]:
        Community.objects.filter(slug=slug).update(is_system=True)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_alter_vote_unique_together_community_is_system_and_more"),
    ]

    operations = [
        migrations.RunPython(mark_system, reverse_code=migrations.RunPython.noop),
    ]
