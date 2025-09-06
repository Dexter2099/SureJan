from unittest.mock import Mock, patch
import os
import requests

from django.core.cache import cache

from core import http_client
from core.utils.thumbnails import resolve_thumbnail, scrape_og_image, fetch_og_image


def _mock_response(text: str = "", status: int = 200) -> Mock:
    resp = Mock()
    resp.text = text
    resp.status_code = status
    def raise_for_status():
        if status >= 400:
            raise requests.HTTPError(response=resp)
    resp.raise_for_status = raise_for_status
    return resp


def test_scraper_returns_og_image_url():
    html = "<html><head><meta property='og:image' content='https://cdn.example/img.jpg'></head></html>"
    resp = _mock_response(html)
    session = http_client.get_session()
    session.get = Mock(return_value=resp)
    with patch("core.http_client.get_session", return_value=session):
        src, alt = resolve_thumbnail("https://example.com", "Preview")
    assert src == "https://cdn.example/img.jpg"
    assert alt == "Preview"
    session.get.assert_called_once_with("https://example.com", timeout=http_client._TIMEOUT)
    headers = session.headers
    assert headers["User-Agent"].startswith("Mozilla/5.0")
    assert headers["Accept-Language"] == "en-US,en;q=0.9"


def test_placeholder_returned_when_missing():
    html = "<html><head></head><body>No OG tags here</body></html>"
    resp = _mock_response(html)
    session = http_client.get_session()
    session.get = Mock(return_value=resp)
    with patch("core.http_client.get_session", return_value=session):
        src, alt = resolve_thumbnail("https://example.com", "Tweet preview")
    assert src.startswith("data:image/svg+xml")
    assert "Tweet preview" in src
    assert alt == "Preview image unavailable"


def test_fallback_when_request_forbidden():
    resp = _mock_response(status=403)
    session = http_client.get_session()
    session.get = Mock(return_value=resp)
    with patch("core.http_client.get_session", return_value=session):
        assert scrape_og_image("https://example.com")[0] is None
        src, alt = resolve_thumbnail("https://example.com", "Forbidden")
    assert src.startswith("data:image/svg+xml")
    assert "Forbidden" in src
    assert alt == "Preview image unavailable"


def test_fetch_og_image_caches_success():
    url = "https://example.com"
    cache.clear()
    with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": ""}):
        with patch("core.utils.thumbnails.scrape_og_image", return_value=("https://cdn.example/img.jpg", 200)) as mock_scrape:
            assert fetch_og_image(url) == "https://cdn.example/img.jpg"
            assert fetch_og_image(url) == "https://cdn.example/img.jpg"
    assert mock_scrape.call_count == 1


def test_fetch_og_image_no_cache_on_error():
    url = "https://example.com"
    cache.clear()
    with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": ""}):
        with patch("core.utils.thumbnails.scrape_og_image", return_value=(None, 500)) as mock_scrape:
            assert fetch_og_image(url) is None
            assert fetch_og_image(url) is None
    # Called twice because error responses are not cached
    assert mock_scrape.call_count == 2
