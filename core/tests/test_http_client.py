import requests
import pytest

from core import http_client


def test_get_session_sets_browser_user_agent(monkeypatch):
    captured = []

    def fake_request(self, method, url, **kwargs):
        captured.append(self.headers.get("User-Agent"))

        class DummyResp:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return {}

        return DummyResp()

    monkeypatch.setattr(requests.Session, "request", fake_request)
    http_client._SESSION = None
    http_client.fetch_json("https://example.com")
    http_client.fetch_html("https://example.com")
    assert len(captured) == 2
    assert all(h.startswith("Mozilla/5.0") for h in captured)
    http_client._SESSION = None


def test_logging_and_counters(monkeypatch, caplog):
    http_client.COUNTERS.clear()

    class DummyResp:
        status_code = 200

        def json(self):
            return {}

        def raise_for_status(self):
            pass

    session = http_client.get_session()
    monkeypatch.setattr(session, "get", lambda url, timeout: DummyResp())
    with caplog.at_level("INFO"):
        http_client.fetch_json("https://example.com/data", source="test")
    assert http_client.COUNTERS["example.com"]["success"] == 1
    assert "provider=example.com" in caplog.text
    assert "Mozilla/5.0" in caplog.text

    class BadResp:
        status_code = 404

    monkeypatch.setattr(session, "get", lambda url, timeout: BadResp())
    with caplog.at_level("WARNING"):
        http_client.fetch_html("https://example.com/miss", source="test")
    assert http_client.COUNTERS["example.com"]["error"] == 1
    assert "status=404" in caplog.text
    assert "Mozilla/5.0" in caplog.text


def test_fetch_og_html_retries_on_timeout(monkeypatch):
    http_client._OG_SESSION = None
    monkeypatch.setattr(http_client, "OG_FETCH_DISABLE_RETRIES", False)
    calls = []

    def fake_get(url, timeout):
        calls.append(1)
        if len(calls) < 3:
            raise requests.exceptions.Timeout()
        return type("R", (), {"status_code": 200})()

    monkeypatch.setattr(http_client, "_robots_allowed", lambda url: True)
    session = http_client.get_og_session()
    monkeypatch.setattr(session, "get", fake_get)
    monkeypatch.setattr(http_client.time, "sleep", lambda s: None)
    resp = http_client.fetch_og_html("https://example.com")
    assert len(calls) == 3
    assert resp.status_code == 200


def test_fetch_og_html_no_retry_on_404(monkeypatch):
    http_client._OG_SESSION = None
    monkeypatch.setattr(http_client, "OG_FETCH_DISABLE_RETRIES", False)
    calls = []

    class Resp:
        status_code = 404

    def fake_get(url, timeout):
        calls.append(1)
        return Resp()

    monkeypatch.setattr(http_client, "_robots_allowed", lambda url: True)
    session = http_client.get_og_session()
    monkeypatch.setattr(session, "get", fake_get)
    monkeypatch.setattr(http_client.time, "sleep", lambda s: None)
    resp = http_client.fetch_og_html("https://example.com")
    assert len(calls) == 1
    assert resp.status_code == 404


def test_fetch_og_html_robots_block(monkeypatch):
    monkeypatch.setattr(http_client, "_robots_allowed", lambda url: False)
    with pytest.raises(PermissionError):
        http_client.fetch_og_html("https://example.com")
