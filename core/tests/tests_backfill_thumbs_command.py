import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.contrib.auth import get_user_model

from core.models import Community, Post
from core.utils import thumbnails


@pytest.mark.django_db
def test_backfill_thumbs_skips_cached_failures(monkeypatch):
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
    )

    def fake_fetch(url):
        return None

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch)
    call_command("backfill_thumbs", limit=1, days=365)
    post.refresh_from_db()
    assert not post.thumbnail_url
    assert cache.get(f"thumbfail:{post.content_url}")

    calls = []

    def fake_fetch2(url):
        calls.append(url)
        return None

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch2)
    call_command("backfill_thumbs", limit=1, days=365)
    assert calls == []
