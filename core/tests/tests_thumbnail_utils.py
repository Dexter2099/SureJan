import pytest
import requests
from django.core.cache import cache
from pathlib import Path
from django.contrib.auth import get_user_model

from core.models import Community, Post
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
def test_fail_ttl_generic(monkeypatch):
    cache.clear()

    def fake_fetch(url):
        fake_fetch.last_status = 500
        return None

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch)

    seen = {}
    orig_set = cache.set

    def fake_set(key, value, timeout):
        seen["timeout"] = timeout
        return orig_set(key, value, timeout)

    monkeypatch.setattr(cache, "set", fake_set)
    thumbnails.resolve_thumbnail("https://example.com", "label", fetch_remote=True)
    assert seen["timeout"] == thumbnails._FAIL_TTL


@pytest.mark.django_db
def test_fail_ttl_throttled(monkeypatch):
    cache.clear()

    def fake_fetch(url):
        fake_fetch.last_status = 429
        return None

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch)

    seen = {}
    orig_set = cache.set

    def fake_set(key, value, timeout):
        seen["timeout"] = timeout
        return orig_set(key, value, timeout)

    monkeypatch.setattr(cache, "set", fake_set)
    thumbnails.resolve_thumbnail("https://example.com", "label", fetch_remote=True)
    assert seen["timeout"] == thumbnails._FAIL_RETRY_TTL


@pytest.mark.django_db
def test_fail_ttl_forbidden(monkeypatch):
    cache.clear()

    def fake_fetch(url):
        fake_fetch.last_status = 403
        return None

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch)

    seen = {}
    orig_set = cache.set

    def fake_set(key, value, timeout):
        seen["timeout"] = timeout
        return orig_set(key, value, timeout)

    monkeypatch.setattr(cache, "set", fake_set)
    thumbnails.resolve_thumbnail("https://example.com", "label", fetch_remote=True)
    assert seen["timeout"] == thumbnails._FAIL_RETRY_TTL


@pytest.mark.django_db
def test_resolve_thumbnail_success_caches(monkeypatch):
    cache.clear()
    og_calls = []
    fb_called = False

    def fake_fetch(url):
        og_calls.append(url)
        return "https://cdn.example/thumb.jpg"

    def fake_fallback(url, fetch_remote):
        nonlocal fb_called
        fb_called = True
        return "https://fallback.example/thumb.jpg"

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch)
    monkeypatch.setattr(thumbnails, "_provider_fallback", fake_fallback)
    url = "https://youtu.be/abc123"
    src, alt = thumbnails.resolve_thumbnail(url, "label", fetch_remote=True)
    assert src == "https://cdn.example/thumb.jpg"
    assert alt == "label"
    assert cache.get("thumb:https://youtube.com/watch?v=abc123") == "https://cdn.example/thumb.jpg"
    assert not fb_called
    og_calls.clear()
    src2, _ = thumbnails.resolve_thumbnail(url, "label", fetch_remote=True)
    assert src2 == "https://cdn.example/thumb.jpg"
    assert og_calls == []


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
def test_resolve_thumbnail_falls_back_after_og(monkeypatch):
    cache.clear()
    order = []

    def fake_fetch(url):
        order.append("og")
        return None

    def fake_fallback(url, fetch_remote):
        order.append("fb")
        return "https://fallback.example/thumb.jpg"

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch)
    monkeypatch.setattr(thumbnails, "_provider_fallback", fake_fallback)

    src, alt = thumbnails.resolve_thumbnail(
        "https://rumble.com/embed/v1abcd", "label", fetch_remote=True
    )
    assert src == "https://fallback.example/thumb.jpg"
    assert alt == "label"
    assert order == ["og", "fb"]
    assert (
        cache.get("thumb:https://rumble.com/v1abcd.html")
        == "https://fallback.example/thumb.jpg"
    )


@pytest.mark.django_db
def test_resolve_thumbnail_direct_canonizes_no_fallback(settings, monkeypatch):
    cache.clear()
    settings.YT_DIRECT_OG = True
    called = {
        "canon": False,
        "fallback": False,
    }

    def fake_cleanup(url):
        called["canon"] = True
        return url

    def fake_fallback(url, fetch_remote):
        called["fallback"] = True
        return "https://example.com/thumb.jpg"

    monkeypatch.setattr(thumbnails, "cleanup_url", fake_cleanup)
    monkeypatch.setattr(thumbnails, "_provider_fallback", fake_fallback)
    monkeypatch.setattr(thumbnails, "fetch_og_image", lambda url: None)

    src, alt = thumbnails.resolve_thumbnail("https://youtu.be/abc123", "label", fetch_remote=True)
    assert src.startswith("data:image/svg+xml")
    assert alt == thumbnails.FALLBACK_ALT
    assert called["canon"] is True
    assert called["fallback"] is False


def _fake_resp(text):
    class Resp:
        status_code = 200

        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            return None

    return Resp(text)


def test_fetch_og_image_from_fixture(monkeypatch):
    html = Path("tests/fixtures/youtube/ogonly.html").read_text()
    monkeypatch.setattr(
        thumbnails,
        "fetch_og_html",
        lambda url, source=None, fallback=False: _fake_resp(html),
    )
    assert (
        thumbnails.fetch_og_image("https://youtu.be/abc123")
        == "https://youtube.example/og.jpg"
    )


def test_x_fallback_thumb_from_fixture(monkeypatch):
    html = Path("tests/fixtures/x/fallback.html").read_text()
    monkeypatch.setattr(
        thumbnails,
        "fetch_og_html",
        lambda url, source=None, fallback=False: _fake_resp(html),
    )
    assert (
        thumbnails.x_fallback_thumb("https://x.com/user/status/1")
        == "https://pbs.twimg.com/media/xyz.jpg"
    )


def test_scrape_og_image_timeout_logs_elapsed(monkeypatch, caplog):
    def fake_fetch(url, source="og-image", fallback=True):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(thumbnails, "fetch_og_html", fake_fetch)

    counter = {"t": 0}

    def fake_monotonic():
        counter["t"] += 1
        return counter["t"]

    monkeypatch.setattr(thumbnails.time, "monotonic", fake_monotonic)

    with caplog.at_level("INFO"):
        thumbnails.scrape_og_image("https://example.com")

    assert "result=http_timeout" in caplog.text
    assert "elapsed=1.00" in caplog.text


@pytest.mark.django_db
def test_resolve_thumbnail_attaches_image(monkeypatch, settings, tmp_path):
    cache.clear()
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.MEDIA_URL = "/media/"
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

    monkeypatch.setattr(
        thumbnails, "fetch_og_image", lambda url: "https://cdn.example.com/thumb.jpg"
    )

    from io import BytesIO
    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (1, 1), "white").save(buf, format="PNG")
    img_bytes = buf.getvalue()

    class Resp:
        status_code = 200
        headers = {"Content-Type": "image/png"}
        content = img_bytes

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        thumbnails, "fetch_og_html", lambda url, source="thumb-fetch": Resp()
    )

    src, alt = thumbnails.resolve_thumbnail(
        post.content_url, "label", fetch_remote=True, post=post
    )
    assert src.startswith(settings.MEDIA_URL)
    post.refresh_from_db()
    assert src == post.image.url
    assert post.image
    assert post.image_thumb
    assert post.thumbnail_alt == "label"
    assert alt == "label"
