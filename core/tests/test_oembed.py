import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from core.models import Community, Post


@pytest.mark.django_db
def test_backfill_thumbs_populates_thumbnail_url(client):
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)
    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Video",
        content_url="https://youtu.be/dQw4w9WgXcQ",
    )
    assert post.thumbnail_url == ""
    call_command("backfill_thumbs", limit=10)
    post.refresh_from_db()
    assert post.thumbnail_url != ""
