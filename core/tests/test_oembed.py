from unittest.mock import Mock, patch

import requests
from django.test import TestCase

from core.oembed import fetch_oembed


def _mock_response(json=None, status=200):
    resp = Mock()
    resp.json.return_value = json

    def raise_for_status():
        if status >= 400:
            raise requests.HTTPError()

    resp.raise_for_status = raise_for_status
    return resp


class OEmbedTests(TestCase):
    def test_fetch_oembed_removes_scripts(self):
        sample_html = '<iframe src="https://youtube.com/embed/abc"></iframe><script>alert(1)</script>'
        with patch("requests.get", return_value=_mock_response(json={"html": sample_html})):
            data = fetch_oembed("https://www.youtube.com/watch?v=abc")
        self.assertEqual(data["type"], "embed")
        self.assertNotIn("script", data["html"].lower())
