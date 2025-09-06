import pytest
from django.core.cache import cache

from core.utils import thumbnails


@pytest.mark.django_db
def test_resolve_thumbnail_failure_caches_and_returns_none(monkeypatch):
    cache.clear()
    calls = []

    def fake_fetch(url):
        calls.append(url)
        return None

    monkeypatch.setattr(thumbnails, "fetch_og_image", fake_fetch)
    url = "https://example.com"
    src, alt = thumbnails.resolve_thumbnail(url, "label", fetch_remote=True)
    assert src is None
    assert alt == thumbnails.FALLBACK_ALT
    assert cache.get(f"thumbfail:{url}")
    calls.clear()
    src2, _ = thumbnails.resolve_thumbnail(url, "label", fetch_remote=True)
    assert src2 is None
    assert calls == []
