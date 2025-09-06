import pytest
from django.test import override_settings

from config import settings as conf_settings


def _build_csp(providers):
    img_src = ["'self'"]
    for p in providers.values():
        img_src.extend(p["img_hosts"])
    img_src.append("data:")
    return {"DIRECTIVES": {"img-src": tuple(img_src), "frame-src": ("'self'",)}}


@pytest.mark.parametrize("provider", ["YOUTUBE", "X", "RUMBLE"])
def test_csp_header_includes_provider_hosts(client, provider):
    providers = {provider: conf_settings.EMBED_PROVIDERS[provider]}
    csp = _build_csp(providers)
    with override_settings(DEBUG=False, EMBED_PROVIDERS=providers, CONTENT_SECURITY_POLICY=csp):
        resp = client.get("/healthz")
    csp_header = resp["Content-Security-Policy"]
    for host in providers[provider]["img_hosts"]:
        assert host in csp_header


def test_csp_header_has_directives(client):
    csp = {
        "DIRECTIVES": {
            "default-src": ("'self'",),
            "img-src": ("'self'", "data:"),
            "frame-src": ("'self'",),
        }
    }
    with override_settings(DEBUG=False, CONTENT_SECURITY_POLICY=csp):
        resp = client.get("/healthz")
    csp_header = resp["Content-Security-Policy"]
    assert "default-src" in csp_header
    assert "img-src" in csp_header
    assert "frame-src" in csp_header


def test_no_legacy_csp_settings():
    assert not hasattr(conf_settings, "CSP_IMG_SRC")
    assert not hasattr(conf_settings, "CSP_FRAME_SRC")


def test_no_legacy_csp_templates():
    from pathlib import Path

    for path in Path("templates").rglob("*.html"):
        text = path.read_text()
        assert "CSP_IMG_SRC" not in text
        assert "CSP_FRAME_SRC" not in text
