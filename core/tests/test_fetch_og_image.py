import requests
import pytest

from core import http_client
from core.utils import thumbnails


def test_scrape_og_image_canonicalization_and_headers(monkeypatch, caplog):
    http_client._OG_SESSION = None
    url = "https://youtu.be/abc123?utm_source=x&fbclid=y"
    captured = {}

    session = requests.Session()
    session.headers.update(http_client.OG_HEADERS)

    def fake_get(url, timeout):
        captured["url"] = url
        captured["headers"] = dict(session.headers)

        class Resp:
            status_code = 200
            text = "<meta property='og:image' content='https://img.test/og.jpg'>"

            def raise_for_status(self):
                pass

        return Resp()

    monkeypatch.setattr(http_client, "get_og_session", lambda: session)
    monkeypatch.setattr(session, "get", fake_get)
    monkeypatch.setattr(http_client, "_robots_allowed", lambda url: True)

    with caplog.at_level("INFO"):
        image, status = thumbnails.scrape_og_image(url)

    assert image == "https://img.test/og.jpg"
    assert status == 200
    assert captured["url"] == "https://youtube.com/watch?v=abc123"
    for k, v in http_client.OG_HEADERS.items():
        assert captured["headers"][k] == v
    assert "provider=youtube.com url=https://youtube.com/watch?v=abc123 status=200 attempt=1" in caplog.text
    assert "provider=youtube.com result=og_found origin_image_url=https://img.test/og.jpg" in caplog.text


def test_fetch_og_html_retries_once_on_timeout(monkeypatch, caplog):
    http_client._OG_SESSION = None
    monkeypatch.setattr(http_client, "OG_FETCH_DISABLE_RETRIES", False)
    calls = []

    def fake_get(url, timeout):
        calls.append(1)
        if len(calls) == 1:
            raise requests.exceptions.Timeout()
        return type("R", (), {"status_code": 200})()

    monkeypatch.setattr(http_client, "_robots_allowed", lambda url: True)
    session = http_client.get_og_session()
    monkeypatch.setattr(session, "get", fake_get)
    monkeypatch.setattr(http_client.time, "sleep", lambda s: None)

    with caplog.at_level("INFO"):
        resp = http_client.fetch_og_html("https://example.com/foo", source="og-image", fallback=True)

    assert resp.status_code == 200
    assert len(calls) == 2
    attempt_logs = [m for m in caplog.messages if "attempt=" in m]
    assert attempt_logs == [
        "provider=example.com url=https://example.com/foo status=timeout attempt=1",
        "provider=example.com url=https://example.com/foo status=200 attempt=2",
    ]


def test_fetch_og_html_no_retry_on_403(monkeypatch, caplog):
    http_client._OG_SESSION = None
    monkeypatch.setattr(http_client, "OG_FETCH_DISABLE_RETRIES", False)
    calls = []

    class Resp:
        status_code = 403

    def fake_get(url, timeout):
        calls.append(1)
        return Resp()

    monkeypatch.setattr(http_client, "_robots_allowed", lambda url: True)
    session = http_client.get_og_session()
    monkeypatch.setattr(session, "get", fake_get)

    with caplog.at_level("INFO"):
        resp = http_client.fetch_og_html("https://example.com/bar", source="og-image", fallback=True)

    assert resp.status_code == 403
    assert len(calls) == 1
    attempt_logs = [m for m in caplog.messages if "attempt=" in m]
    assert attempt_logs == [
        "provider=example.com url=https://example.com/bar status=403 attempt=1"
    ]
    summary_logs = [m for m in caplog.messages if "reason=" in m]
    assert summary_logs and summary_logs[-1].endswith("reason=http_403 fallback=True")


def test_fetch_og_image_canonical_url_used_in_cache(monkeypatch):
    url = "https://youtu.be/abc123?utm_source=x"
    captured = {}

    session = requests.Session()
    session.headers.update(http_client.OG_HEADERS)

    def fake_get(url, timeout):
        captured["url"] = url

        class Resp:
            status_code = 200
            text = "<meta property='og:image' content='https://img.test/og.jpg'>"

            def raise_for_status(self):
                pass

        return Resp()

    monkeypatch.setattr(http_client, "get_og_session", lambda: session)
    monkeypatch.setattr(session, "get", fake_get)
    monkeypatch.setattr(http_client, "_robots_allowed", lambda url: True)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    class FakeCache:
        def __init__(self):
            self.last = {}
        def get(self, key):
            return None
        def set(self, key, value, timeout):
            self.last = {"key": key, "value": value}

    fake_cache = FakeCache()
    monkeypatch.setattr(thumbnails, "cache", fake_cache)

    result = thumbnails.fetch_og_image(url)
    expected = "https://youtube.com/watch?v=abc123"
    assert result == "https://img.test/og.jpg"
    assert captured["url"] == expected
    assert fake_cache.last["key"] == f"og-image:{expected}"
    assert fake_cache.last["value"] == "https://img.test/og.jpg"
