from django.db import migrations, models
from django.utils.text import slugify


def backfill_slugs(apps, schema_editor):
    Post = apps.get_model("core", "Post")
    for post in Post.objects.filter(models.Q(slug__isnull=True) | models.Q(slug="")):
        base = slugify(post.title)[:191]
        slug = base
        i = 0
        while Post.objects.filter(community_id=post.community_id, slug=slug).exclude(pk=post.pk).exists():
            i += 1
            slug = f"{base}-{post.id}" if i == 1 else f"{base}-{post.id}-{i}"
            slug = slug[:191]
        post.slug = slug
        post.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0031b_schema_updates"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL("ALTER TABLE core_post DROP COLUMN IF EXISTS embed_html"),
                migrations.RunSQL("ALTER TABLE core_post DROP COLUMN IF EXISTS embed_id"),
                migrations.RunSQL("DROP TABLE IF EXISTS core_embed"),
                migrations.RunSQL("ALTER TABLE core_post DROP COLUMN IF EXISTS image"),
                migrations.RunSQL("ALTER TABLE core_post DROP COLUMN IF EXISTS image_thumb"),
                migrations.RunSQL("ALTER TABLE core_post DROP COLUMN IF EXISTS thumbnail_url"),
                migrations.RunSQL("ALTER TABLE core_post DROP COLUMN IF EXISTS thumbnail_alt"),
            ],
            state_operations=[
                migrations.RemoveField(model_name="post", name="image"),
                migrations.RemoveField(model_name="post", name="image_thumb"),
            ],
        ),
        migrations.RunPython(backfill_slugs, migrations.RunPython.noop),
        migrations.RunSQL("ALTER TABLE core_post ALTER COLUMN slug SET NOT NULL"),
        migrations.AlterField(
            model_name="post",
            name="slug",
            field=models.SlugField(max_length=191),
        ),
        migrations.AddConstraint(
            model_name="post",
            constraint=models.UniqueConstraint(
                fields=["community", "slug"], name="uniq_post_community_slug"
            ),
        ),
    ]
