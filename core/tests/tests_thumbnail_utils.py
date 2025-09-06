import pytest
from django.core.cache import cache

from core.utils import thumbnails


@pytest.mark.django_db
def test_resolve_thumbnail_failure_caches_and_returns_placeholder(monkeypatch):
    cache.clear()
    calls = []

    def fake_fetch(url):
        calls.append(url)
        return None

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch)
    url = "https://example.com"
    src, alt = thumbnails.resolve_thumbnail(url, "label", fetch_remote=True)
    assert src.startswith("data:image/svg+xml")
    assert alt == thumbnails.FALLBACK_ALT
    assert cache.get(f"thumbfail:{url}")
    calls.clear()
    src2, _ = thumbnails.resolve_thumbnail(url, "label", fetch_remote=True)
    assert src2.startswith("data:image/svg+xml")
    assert calls == []


@pytest.mark.django_db
def test_resolve_thumbnail_success_caches(monkeypatch):
    cache.clear()
    calls = []

    def fake_fetch(url):
        calls.append(url)
        return "https://example.com/thumb.jpg"

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch)
    url = "https://example.com"
    src, alt = thumbnails.resolve_thumbnail(url, "label", fetch_remote=True)
    assert src == "https://example.com/thumb.jpg"
    assert alt == "label"
    assert cache.get(f"thumb:{url}") == "https://example.com/thumb.jpg"
    calls.clear()
    src2, _ = thumbnails.resolve_thumbnail(url, "label", fetch_remote=True)
    assert src2 == "https://example.com/thumb.jpg"
    assert calls == []


def test_resolve_thumbnail_canonicalizes_url(monkeypatch):
    cache.clear()
    seen = []

    monkeypatch.setattr(thumbnails, "fetch_og_image", lambda url: None)

    def fake_youtube(url, fetch_remote=False):
        seen.append(url)
        return None

    monkeypatch.setattr(thumbnails, "youtube_fallback_thumb", fake_youtube)

    thumbnails.resolve_thumbnail("https://youtu.be/abc123?t=9", "label", fetch_remote=True)
    assert seen[0] == "https://youtube.com/watch?v=abc123"
    assert cache.get("thumbfail:https://youtube.com/watch?v=abc123")


@pytest.mark.django_db
def test_resolve_thumbnail_direct_skips_canon_and_fallback(settings, monkeypatch):
    cache.clear()
    settings.YT_DIRECT_OG = True
    called = {
        "canon": False,
        "fallback": False,
    }

    def fake_canon(url):
        called["canon"] = True
        return url

    def fake_fallback(url, fetch_remote):
        called["fallback"] = True
        return "https://example.com/thumb.jpg"

    monkeypatch.setattr(thumbnails, "canonicalize_video_url", fake_canon)
    monkeypatch.setattr(thumbnails, "_provider_fallback", fake_fallback)
    monkeypatch.setattr(thumbnails, "fetch_og_image", lambda url: None)

    src, alt = thumbnails.resolve_thumbnail("https://youtu.be/abc123", "label", fetch_remote=True)
    assert src.startswith("data:image/svg+xml")
    assert alt == thumbnails.FALLBACK_ALT
    assert called["canon"] is False
    assert called["fallback"] is False
