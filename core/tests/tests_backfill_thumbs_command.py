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


@pytest.mark.django_db
def test_backfill_thumbs_og_first_and_caches_canonical(monkeypatch):
    cache.clear()
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)
    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Link",
        content_url="https://youtu.be/abc123",
    )

    fb_called = False

    def fake_fetch(url):
        return "https://cdn.example.com/thumb.jpg"

    def fake_fallback(url, fetch_remote):
        nonlocal fb_called
        fb_called = True
        return "https://fallback.example.com/thumb.jpg"

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch)
    monkeypatch.setattr(thumbnails, "_provider_fallback", fake_fallback)
    call_command("backfill_thumbs", limit=1, days=365)
    post.refresh_from_db()
    assert post.thumbnail_url == "https://cdn.example.com/thumb.jpg"
    assert cache.get("thumb:https://youtube.com/watch?v=abc123") == "https://cdn.example.com/thumb.jpg"
    assert fb_called is False


@pytest.mark.django_db
def test_backfill_thumbs_uses_fallback_after_og(monkeypatch):
    cache.clear()
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)
    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Link",
        content_url="https://rumble.com/embed/v1abcd",
    )

    order = []

    def fake_fetch(url):
        order.append("og")
        return None

    def fake_fallback(url, fetch_remote):
        order.append("fb")
        return "https://fallback.example.com/thumb.jpg"

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch)
    monkeypatch.setattr(thumbnails, "_provider_fallback", fake_fallback)
    call_command("backfill_thumbs", limit=1, days=365)
    post.refresh_from_db()
    assert post.thumbnail_url == "https://fallback.example.com/thumb.jpg"
    assert order == ["og", "fb"]
    assert (
        cache.get("thumb:https://rumble.com/v1abcd.html")
        == "https://fallback.example.com/thumb.jpg"
    )


@pytest.mark.django_db
def test_backfill_thumbs_caches_rumble_thumbnails(monkeypatch):
    cache.clear()
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)
    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Link",
        content_url="https://rumble.com/v1abc",
        thumbnail_url="https://sp.rmbl.ws/s8/1/v1abc.jpg",
    )

    from core.management.commands import backfill_thumbs

    def fake_cache(origin_url):
        return "/media/thumbs/rumble/cache.jpg"

    monkeypatch.setattr(backfill_thumbs, "cache_remote_image", fake_cache)
    call_command("backfill_thumbs", days=365)
    post.refresh_from_db()
    assert post.thumbnail_url == "/media/thumbs/rumble/cache.jpg"

    post.thumbnail_url = "https://sp.rmbl.ws/s8/1/v1abc.jpg"
    post.save(update_fields=["thumbnail_url"])
    calls: list[str] = []

    def fake_cache2(origin_url):
        calls.append(origin_url)
        return "/media/thumbs/rumble/cache2.jpg"

    monkeypatch.setattr(backfill_thumbs, "cache_remote_image", fake_cache2)
    call_command("backfill_thumbs", days=365, dry_run=True)
    post.refresh_from_db()
    assert post.thumbnail_url == "https://sp.rmbl.ws/s8/1/v1abc.jpg"
    assert calls == ["https://sp.rmbl.ws/s8/1/v1abc.jpg"]
