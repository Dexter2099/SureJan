from django.db import migrations


def resolve_slug_collisions(apps, schema_editor):
    Post = apps.get_model("core", "Post")
    from django.db.models import Count

    duplicates = (
        Post.objects.values("community_id", "slug")
        .annotate(ct=Count("id"))
        .filter(ct__gt=1)
    )

    for dup in duplicates:
        community_id = dup["community_id"]
        slug = dup["slug"]
        posts = list(
            Post.objects.filter(community_id=community_id, slug=slug).order_by("id")
        )
        used = set(
            Post.objects.filter(community_id=community_id).values_list("slug", flat=True)
        )
        suffix = 1
        for post in posts[1:]:
            def build_slug(sfx):
                base = slug[: 191 - len(f"-{sfx}")]
                return f"{base}-{sfx}"

            new_slug = build_slug(suffix)
            while new_slug in used:
                suffix += 1
                new_slug = build_slug(suffix)
            post.slug = new_slug
            post.save(update_fields=["slug"])
            used.add(new_slug)
            suffix += 1


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0031a_populate_slugs"),
    ]

    operations = [migrations.RunPython(resolve_slug_collisions, noop)]
