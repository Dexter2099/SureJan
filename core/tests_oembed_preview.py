import os
import requests
from unittest.mock import Mock, patch
from django.urls import reverse
from django.test import Client

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.views import fetch_oembed


def _mock_response(json=None, text="", status=200):
    resp = Mock()
    resp.json.return_value = json
    resp.text = text
    def raise_for_status():
        if status >= 400:
            raise requests.HTTPError()
    resp.raise_for_status = raise_for_status
    return resp


def test_fetch_oembed_youtube_removes_scripts():
    sample_html = '<iframe src="https://youtube.com/embed/abc"></iframe><script>alert(1)</script>'
    with patch("requests.get", return_value=_mock_response(json={"html": sample_html})):
        data = fetch_oembed("https://www.youtube.com/watch?v=abc")
    assert data["type"] == "embed"
    assert "script" not in data["html"].lower()


def test_fetch_oembed_falls_back_to_link_card():
    def side_effect(url, *args, **kwargs):
        if "oembed" in url:
            raise requests.RequestException()
        return _mock_response(text="<title>Example Domain</title>")
    with patch("requests.get", side_effect=side_effect):
        data = fetch_oembed("https://example.com")
    assert data["type"] == "link"
    assert data["domain"] == "example.com"
    assert data["title"] == "Example Domain"


def test_oembed_preview_view_uses_helper():
    client = Client()
    with patch("core.views.fetch_oembed", return_value={"type": "link", "domain": "example.com", "favicon": "f", "url": "https://example.com", "title": "Example"}) as mock_fetch:
        resp = client.post(reverse("oembed_preview"), {"url": "https://example.com"}, HTTP_HOST="localhost")
    assert resp.status_code == 200
    assert "example.com" in resp.content.decode()
    mock_fetch.assert_called_once()
