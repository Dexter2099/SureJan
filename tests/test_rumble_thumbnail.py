import json
from pathlib import Path

from core.utils import thumbnails

FIXTURES = Path(__file__).parent / "fixtures" / "rumble"


def load(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_rumble_thumbnail_oembed(monkeypatch):
    data = json.loads(load("oembed.json"))

    def fake_fetch_json(url, source=""):
        return data

    called = []

    def fake_fetch_html(url, source=""):
        called.append(url)
        class Resp:
            status_code = 200
            text = ""
            def raise_for_status(self):
                pass
        return Resp()

    monkeypatch.setattr(thumbnails, "fetch_json", fake_fetch_json)
    monkeypatch.setattr(thumbnails, "fetch_html", fake_fetch_html)

    thumb = thumbnails.rumble_thumbnail("https://rumble.com/v1")
    assert thumb == "https://rumble.example/thumb.jpg"
    assert called == []


def test_rumble_thumbnail_html_fallback(monkeypatch):
    def fake_fetch_json(url, source=""):
        raise Exception("boom")

    html = load("fallback.html")

    class Resp:
        status_code = 200
        text = html
        def raise_for_status(self):
            pass

    monkeypatch.setattr(thumbnails, "fetch_json", fake_fetch_json)
    monkeypatch.setattr(thumbnails, "fetch_html", lambda url, source="": Resp())

    thumb = thumbnails.rumble_thumbnail("https://rumble.com/v1")
    assert thumb == "https://rumble.example/secure.jpg"


def test_rumble_thumbnail_failure(monkeypatch):
    def fake_fetch_json(url, source=""):
        raise Exception("boom")

    html = load("nothumb.html")

    class Resp:
        status_code = 200
        text = html
        def raise_for_status(self):
            pass

    monkeypatch.setattr(thumbnails, "fetch_json", fake_fetch_json)
    monkeypatch.setattr(thumbnails, "fetch_html", lambda url, source="": Resp())

    assert thumbnails.rumble_thumbnail("https://rumble.com/v1") is None


def test_resolve_thumbnail_rumble(monkeypatch):
    monkeypatch.setattr(
        thumbnails, "rumble_thumbnail", lambda url: "https://rumble.example/thumb.jpg"
    )
    src, alt = thumbnails.resolve_thumbnail(
        "https://rumble.com/v1", "label", fetch_remote=True
    )
    assert src == "https://rumble.example/thumb.jpg"
    assert alt == "label"
