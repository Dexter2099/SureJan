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

    cache.delete(f"thumbfail:{post.content_url}")

    def fake_fetch3(url):
        return "https://cdn.example.com/thumb.jpg"

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch3)
    call_command("backfill_thumbs", limit=1, days=365)
    post.refresh_from_db()
    assert post.thumbnail_url == "https://cdn.example.com/thumb.jpg"
    assert post.thumbnail_alt == post.title


@pytest.mark.django_db
def test_backfill_thumbs_rejects_http(monkeypatch):
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

    def fake_resolve(url, label, fetch_remote=False):
        return "http://insecure/thumb.jpg", "alt"

    monkeypatch.setattr(thumbnails, "resolve_thumbnail", fake_resolve)
    call_command("backfill_thumbs", limit=1, days=365)
    post.refresh_from_db()
    assert not post.thumbnail_url


@pytest.mark.django_db
def test_backfill_thumbs_canonicalizes_fail_key(monkeypatch):
    cache.clear()
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)
    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Link",
        content_url="https://youtu.be/abc123?t=1",
    )

    cache.set("thumbfail:https://youtube.com/watch?v=abc123", True, 60)

    calls = []

    def fake_resolve(url, label, fetch_remote=False):
        calls.append(url)
        return None, "alt"

    monkeypatch.setattr(thumbnails, "resolve_thumbnail", fake_resolve)
    call_command("backfill_thumbs", limit=1, days=365)
    assert calls == []
