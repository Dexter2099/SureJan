from unittest.mock import patch, Mock

import requests

from core.utils.thumbnails import resolve_thumbnail, scrape_og_image, REQUEST_HEADERS


def _mock_response(text: str) -> Mock:
    resp = Mock()
    resp.text = text
    resp.raise_for_status = lambda: None
    return resp


def _mock_error_response(status_code: int) -> Mock:
    resp = Mock()
    def raise_error():
        raise requests.HTTPError(response=Mock(status_code=status_code))
    resp.raise_for_status = raise_error
    return resp


def test_scraper_returns_og_image_url():
    html = "<html><head><meta property='og:image' content='https://cdn.example/img.jpg'></head></html>"
    with patch("core.utils.thumbnails.requests.get", return_value=_mock_response(html)) as mock_get:
        url = "https://example.com"
        src, alt = resolve_thumbnail(url, "Preview")
        assert src == "https://cdn.example/img.jpg"
        assert alt == "Preview"
        mock_get.assert_called_once_with(url, timeout=5, headers=REQUEST_HEADERS)


def test_placeholder_returned_when_missing():
    html = "<html><head></head><body>No OG tags here</body></html>"
    with patch("core.utils.thumbnails.requests.get", return_value=_mock_response(html)):
        src, alt = resolve_thumbnail("https://example.com", "Tweet preview")
        assert src.startswith("data:image/svg+xml")
        assert "Tweet preview" in src
        assert alt == "Preview image unavailable"


def test_fallback_when_request_forbidden():
    url = "https://example.com"
    with patch("core.utils.thumbnails.requests.get", return_value=_mock_error_response(403)):
        assert scrape_og_image(url) is None
        src, alt = resolve_thumbnail(url, "Forbidden")
        assert src.startswith("data:image/svg+xml")
        assert "Forbidden" in src
        assert alt == "Preview image unavailable"
