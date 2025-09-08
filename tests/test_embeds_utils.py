import logging
import os
import sys
from unittest.mock import Mock

import pytest
from requests.exceptions import HTTPError, Timeout

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from embeds.utils import PLACEHOLDER_URL, get_thumbnail_url


def test_get_thumbnail_url_http_error(monkeypatch, caplog):
    def fake_get(*args, **kwargs):
        response = Mock(status_code=503)
        raise HTTPError(response=response)

    monkeypatch.setattr("embeds.utils.requests.get", fake_get)

    with caplog.at_level(logging.WARNING):
        assert get_thumbnail_url("https://example.com") == PLACEHOLDER_URL
    assert "503" in caplog.text


def test_get_thumbnail_url_timeout(monkeypatch, caplog):
    def fake_get(*args, **kwargs):
        raise Timeout("boom")

    monkeypatch.setattr("embeds.utils.requests.get", fake_get)

    with caplog.at_level(logging.WARNING):
        assert get_thumbnail_url("https://example.com") == PLACEHOLDER_URL
    assert "boom" in caplog.text
