"""Reintroduce Post.image and optional image_thumb fields safely."""

from django.db import migrations, models


def add_image_fields(apps, schema_editor):
    Post = apps.get_model("core", "Post")
    table = Post._meta.db_table
    qn = schema_editor.quote_name
    with schema_editor.connection.cursor() as cursor:
        existing = {col.name for col in schema_editor.connection.introspection.get_table_description(cursor, table)}
    statements = []
    if "image" not in existing:
        statements.append(
            f"ALTER TABLE {qn(table)} ADD COLUMN {qn('image')} varchar(100)"
        )
    if "image_thumb" not in existing:
        statements.append(
            f"ALTER TABLE {qn(table)} ADD COLUMN {qn('image_thumb')} varchar(100)"
        )
    for sql in statements:
        schema_editor.execute(sql)


def remove_image_fields(apps, schema_editor):
    Post = apps.get_model("core", "Post")
    table = Post._meta.db_table
    qn = schema_editor.quote_name
    with schema_editor.connection.cursor() as cursor:
        existing = {col.name for col in schema_editor.connection.introspection.get_table_description(cursor, table)}
    statements = []
    if "image_thumb" in existing:
        statements.append(
            f"ALTER TABLE {qn(table)} DROP COLUMN {qn('image_thumb')}"
        )
    if "image" in existing:
        statements.append(
            f"ALTER TABLE {qn(table)} DROP COLUMN {qn('image')}"
        )
    for sql in statements:
        schema_editor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0031c_remove_post_image_remove_post_image_thumb_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_image_fields, remove_image_fields)
            ],
            state_operations=[
                migrations.AddField(
                    model_name="post",
                    name="image",
                    field=models.ImageField(upload_to="posts/", null=True, blank=True),
                ),
                migrations.AddField(
                    model_name="post",
                    name="image_thumb",
                    field=models.ImageField(upload_to="posts/thumbs/", null=True, blank=True),
                ),
            ],
        )
    ]
