import requests

from core import http_client


def test_get_session_sets_browser_user_agent(monkeypatch):
    captured = []

    def fake_request(self, method, url, **kwargs):
        captured.append(self.headers.get("User-Agent"))

        class DummyResp:
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
