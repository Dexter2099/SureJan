from django.db import migrations


class Migration(migrations.Migration):
    """
    History shim: recreates the missing migration id so ordering is consistent.
    No schema ops.
    """

    dependencies = [
        ("core", "0002_delete_comment"),
    ]

    operations = [
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop),
    ]
