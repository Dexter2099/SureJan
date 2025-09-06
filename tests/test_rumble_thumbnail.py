from core.utils import thumbnails


def test_resolve_thumbnail_rumble(monkeypatch):
    monkeypatch.setattr(thumbnails, "fetch_og_image", lambda url: None)
    monkeypatch.setattr(
        thumbnails, "rumble_fallback_thumb", lambda url: "https://rumble.example/thumb.jpg"
    )
    src, alt = thumbnails.resolve_thumbnail(
        "https://rumble.com/v1", "label", fetch_remote=True
    )
    assert src == "https://rumble.example/thumb.jpg"
    assert alt == "label"


def test_resolve_thumbnail_rumble_rejects_http(monkeypatch):
    monkeypatch.setattr(thumbnails, "fetch_og_image", lambda url: None)
    monkeypatch.setattr(
        thumbnails, "rumble_fallback_thumb", lambda url: "http://rumble.example/thumb.jpg"
    )
    src, alt = thumbnails.resolve_thumbnail(
        "https://rumble.com/v1", "label", fetch_remote=True
    )
    assert src.startswith("data:image/svg+xml")
    assert alt == thumbnails.FALLBACK_ALT
