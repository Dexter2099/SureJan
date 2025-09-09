from django.db import migrations


class Migration(migrations.Migration):
    """
    History shim: recreates the missing migration id so dependent apps (comments.0001)
    see core.0002 as present. No schema ops.
    """

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop),
    ]
