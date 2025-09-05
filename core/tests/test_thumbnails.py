from unittest.mock import patch, Mock

from core.utils.thumbnails import resolve_thumbnail


def _mock_response(text: str) -> Mock:
    resp = Mock()
    resp.text = text
    resp.raise_for_status = lambda: None
    return resp


def test_scraper_returns_og_image_url():
    html = "<html><head><meta property='og:image' content='https://cdn.example/img.jpg'></head></html>"
    with patch("core.utils.thumbnails.requests.get", return_value=_mock_response(html)) as mock_get:
        url = "https://example.com"
        assert resolve_thumbnail(url, "Preview") == "https://cdn.example/img.jpg"
        mock_get.assert_called_once_with(url, timeout=5)


def test_placeholder_returned_when_missing():
    html = "<html><head></head><body>No OG tags here</body></html>"
    with patch("core.utils.thumbnails.requests.get", return_value=_mock_response(html)):
        result = resolve_thumbnail("https://example.com", "Tweet preview")
        assert result.startswith("data:image/svg+xml")
        assert "Tweet preview" in result
