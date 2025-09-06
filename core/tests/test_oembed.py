from unittest.mock import Mock, patch
import requests
from django.core.cache import cache
from django.test import TestCase

from core import http_client
from core.oembed import fetch_oembed


def _mock_json_response(data=None, status=200):
    resp = Mock()
    resp.status_code = status
    resp.json.return_value = data or {}
    def raise_for_status():
        if status >= 400:
            raise requests.HTTPError(response=resp)
    resp.raise_for_status = raise_for_status
    return resp


def _mock_html_response(text="", status=200):
    resp = Mock()
    resp.status_code = status
    resp.text = text
    def raise_for_status():
        if status >= 400:
            raise requests.HTTPError(response=resp)
    resp.raise_for_status = raise_for_status
    return resp


class OEmbedTests(TestCase):
    def test_fetch_oembed_removes_scripts(self):
        sample_html = '<iframe src="https://youtube.com/embed/abc"></iframe><script>alert(1)</script>'
        resp = _mock_json_response({"html": sample_html})
        http_client._SESSION = None
        session = http_client.get_session()
        session.get = Mock(return_value=resp)
        with patch("core.http_client.get_session", return_value=session):
            data = fetch_oembed("https://www.youtube.com/watch?v=abc")
        self.assertEqual(data["type"], "embed")
        self.assertNotIn("script", data["html"].lower())
        session.get.assert_called_once()
        headers = session.headers
        self.assertTrue(headers["User-Agent"].startswith("Mozilla/5.0"))
        self.assertEqual(headers["Accept-Language"], "en-US,en;q=0.9")

    def test_fetch_oembed_caches_success(self):
        url = "https://www.youtube.com/watch?v=abc"
        cache.clear()
        sample_html = "<iframe></iframe>"
        with patch("core.oembed.fetch_json", return_value={"html": sample_html}) as mock_json:
            fetch_oembed(url)
            fetch_oembed(url)
        self.assertEqual(mock_json.call_count, 1)

    def test_fetch_oembed_no_cache_on_error(self):
        url = "https://www.youtube.com/watch?v=abc"
        cache.clear()
        def raise_http_error(*args, **kwargs):
            raise requests.HTTPError(response=Mock(status_code=500))
        with patch("core.oembed.fetch_json", side_effect=raise_http_error) as mock_json, \
             patch("core.oembed.fetch_html", return_value=_mock_html_response("<title>t</title>")):
            fetch_oembed(url)
            fetch_oembed(url)
        self.assertEqual(mock_json.call_count, 2)

    def test_fetch_oembed_logs_provider_host(self):
        http_client.COUNTERS.clear()
        cache.clear()
        resp = _mock_json_response({"html": "<iframe></iframe>"})
        http_client._SESSION = None
        session = http_client.get_session()
        session.get = Mock(return_value=resp)
        with patch("core.http_client.get_session", return_value=session):
            fetch_oembed("https://www.youtube.com/watch?v=xyz")
        self.assertEqual(http_client.COUNTERS["www.youtube.com"]["success"], 1)
