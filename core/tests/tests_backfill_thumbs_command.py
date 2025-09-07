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
    assert not post.image
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
    from core.management.commands import backfill_thumbs as backfill_mod

    def fake_persist(post_obj, img_url, label):
        Post.objects.filter(pk=post_obj.pk).update(image="thumb.jpg", image_thumb="thumb.jpg")
        post_obj.image = "thumb.jpg"

    monkeypatch.setattr(backfill_mod, "persist_thumbnail", fake_persist)
    call_command("backfill_thumbs", limit=1, days=365)
    post.refresh_from_db()
    assert post.image.name == "thumb.jpg"


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
    assert not post.image


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
    from core.management.commands import backfill_thumbs as backfill_mod

    def fake_persist(post_obj, img_url, label):
        Post.objects.filter(pk=post_obj.pk).update(image="thumb.jpg", image_thumb="thumb.jpg")
        post_obj.image = "thumb.jpg"

    monkeypatch.setattr(backfill_mod, "persist_thumbnail", fake_persist)
    call_command("backfill_thumbs", limit=1, days=365)
    post.refresh_from_db()
    assert post.image.name == "thumb.jpg"
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
    persist_calls = []
    from core.management.commands import backfill_thumbs as backfill_mod

    def fake_persist(post_obj, img_url, label):
        persist_calls.append(img_url)
        Post.objects.filter(pk=post_obj.pk).update(image="thumb.jpg", image_thumb="thumb.jpg")
        post_obj.image = "thumb.jpg"

    monkeypatch.setattr(backfill_mod, "persist_thumbnail", fake_persist)
    call_command("backfill_thumbs", limit=1, days=365)
    post.refresh_from_db()
    assert persist_calls == ["https://fallback.example.com/thumb.jpg"]
    assert order == ["og", "fb"]
    assert (
        cache.get("thumb:https://rumble.com/v1abcd.html")
        == "https://fallback.example.com/thumb.jpg"
    )


