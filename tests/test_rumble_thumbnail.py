import hashlib

from django.conf import settings
from django.core.cache import cache
from django.test import override_settings

from core.utils import thumbnails


def test_resolve_thumbnail_rumble(monkeypatch, tmp_path):
    cache.clear()
    remote_url = "https://sp.rmbl.ws/s8/1/testslug.jpg"

    monkeypatch.setattr(thumbnails, "fetch_og_image", lambda url: None)
    monkeypatch.setattr(thumbnails, "rumble_fallback_thumb", lambda url: remote_url)

    class Resp:
        status_code = 200
        headers = {"Content-Type": "image/jpeg"}
        content = b"img"

        def raise_for_status(self):
            pass

    calls = []

    def fake_fetch_og_html(url, source="unknown"):
        calls.append(url)
        return Resp()

    monkeypatch.setattr(thumbnails, "fetch_og_html", fake_fetch_og_html)

    url = "https://rumble.com/v1"
    digest = hashlib.sha1(remote_url.encode("utf-8")).hexdigest()

    with override_settings(
        MEDIA_ROOT=tmp_path / "media",
        THUMB_CACHE_DIR=tmp_path / "media" / "thumbs",
        MEDIA_URL="/media/",
    ):
        expected = settings.THUMB_CACHE_DIR / "rumble" / f"{digest}.jpg"

        src, alt = thumbnails.resolve_thumbnail(url, "label", fetch_remote=True)
        assert src.startswith(settings.MEDIA_URL)
        assert src.endswith(expected.name)
        assert expected.exists()
        assert alt == "label"
        assert calls == [remote_url]

        calls.clear()
        src2, _ = thumbnails.resolve_thumbnail(url, "label", fetch_remote=True)
        assert src2 == src
        assert calls == []

def test_resolve_thumbnail_rumble_rejects_http(monkeypatch):
    cache.clear()
    monkeypatch.setattr(thumbnails, "fetch_og_image", lambda url: None)
    monkeypatch.setattr(
        thumbnails, "rumble_fallback_thumb", lambda url: "http://rumble.example/thumb.jpg"
    )
    src, alt = thumbnails.resolve_thumbnail(
        "https://rumble.com/v1", "label", fetch_remote=True
    )
    assert src.startswith("data:image/svg+xml")
    assert alt == thumbnails.FALLBACK_ALT


def test_resolve_thumbnail_rumble_direct_og_cached(monkeypatch, tmp_path):
    cache.clear()
    remote_url = "https://sp.rmbl.ws/s8/1/testslug.jpg"

    def fake_fetch_og(url):
        thumbnails.fetch_og_image.last_status = 200
        return remote_url

    class Resp:
        status_code = 200
        headers = {"Content-Type": "image/jpeg"}
        content = b"img"

        def raise_for_status(self):
            pass

    calls = []

    def fake_fetch_og_html(url, source="unknown"):
        calls.append(url)
        return Resp()

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch_og)
    monkeypatch.setattr(thumbnails, "fetch_og_html", fake_fetch_og_html)

    url = "https://rumble.com/v1abc"
    digest = hashlib.sha1(remote_url.encode("utf-8")).hexdigest()

    with override_settings(
        RUMBLE_DIRECT_OG=True,
        MEDIA_ROOT=tmp_path / "media",
        THUMB_CACHE_DIR=tmp_path / "media" / "thumbs",
        MEDIA_URL="/media/",
    ):
        expected = settings.THUMB_CACHE_DIR / "rumble" / f"{digest}.jpg"

        src, _ = thumbnails.resolve_thumbnail(url, "label", fetch_remote=True)
        assert src.startswith(settings.MEDIA_URL)
        assert src.endswith(expected.name)
        assert expected.exists()
        assert calls == [remote_url]

        src2, _ = thumbnails.resolve_thumbnail(url, "label", fetch_remote=True)
        assert src2 == src
        assert calls == [remote_url]


def test_resolve_thumbnail_rumble_direct_og_error(monkeypatch, settings, tmp_path):
    cache.clear()
    settings.RUMBLE_DIRECT_OG = True
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.THUMB_CACHE_DIR = settings.MEDIA_ROOT / "thumbs"
    settings.MEDIA_URL = "/media/"

    remote_url = "https://sp.rmbl.ws/s8/1/testslug.jpg"

    def fake_fetch_og(url):
        thumbnails.fetch_og_image.last_status = 200
        return remote_url

    class Resp:
        status_code = 500
        headers = {"Content-Type": "image/jpeg"}
        content = b""

        def raise_for_status(self):
            raise Exception("boom")

    def fake_fetch_og_html(url, source="unknown"):
        return Resp()

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch_og)
    monkeypatch.setattr(thumbnails, "fetch_og_html", fake_fetch_og_html)

    src, alt = thumbnails.resolve_thumbnail("https://rumble.com/v1abc", "label", fetch_remote=True)
    assert src.startswith("data:image/svg+xml")
    assert alt == thumbnails.FALLBACK_ALT
