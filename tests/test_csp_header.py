import pytest
from django.test import override_settings


def test_csp_header_includes_img_src_hosts(client):
    csp = {
        "DIRECTIVES": {
            "img-src": (
                "'self'",
                "https:",
                "https://*.twimg.com",
                "https://i.ytimg.com",
                "https://*.rumble.com",
                "https://*.rumblecdn.com",
                "data:",
            )
        }
    }
    with override_settings(DEBUG=False, CONTENT_SECURITY_POLICY=csp):
        resp = client.get("/healthz")
    csp_header = resp["Content-Security-Policy"]
    assert "https://*.rumble.com" in csp_header
    assert "https://*.rumblecdn.com" in csp_header
    assert "https://*.twimg.com" in csp_header
    assert "https://i.ytimg.com" in csp_header
