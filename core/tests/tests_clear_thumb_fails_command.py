import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.contrib.auth import get_user_model

from core.models import Community, Post
from core.utils import thumbnails


@pytest.mark.django_db
def test_clear_thumb_fails_command(monkeypatch):
    cache.clear()
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)
    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Link",
        content_url="https://example.com",
        thumbnail_url="data:image/svg+xml;base64,abc",
        thumbnail_alt="Preview",
    )
    cache.set("thumbfail:https://example.com", True, 60)

    call_command("clear_thumb_fails")

    post.refresh_from_db()
    assert post.thumbnail_url == ""
    assert post.thumbnail_alt == ""
    assert cache.get("thumbfail:https://example.com") is None

    def fake_fetch(url):
        return "https://cdn.example.com/thumb.jpg"

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch)
    call_command("backfill_thumbs", limit=1, days=365)
    post.refresh_from_db()
    assert post.thumbnail_url == "https://cdn.example.com/thumb.jpg"
    assert post.thumbnail_alt == post.title
