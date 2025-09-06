import pytest
from django.test import override_settings

from config import settings as conf_settings


def _build_csp(providers):
    img_src = ["'self'"]
    for p in providers.values():
        img_src.extend(p["img_hosts"])
    img_src.append("data:")
    return {"DIRECTIVES": {"img-src": tuple(img_src)}}


@pytest.mark.parametrize(
    "provider,expected_hosts",
    [
        ("YOUTUBE", ["https://*.ytimg.com"]),
        ("X", ["https://*.twimg.com", "https://pbs.twimg.com"]),
        (
            "RUMBLE",
            [
                "https://rumblecdn.com",
                "https://*.rumblecdn.com",
                "https://i.rmbl.ws",
                "https://*.rmbl.ws",
            ],
        ),
    ],
)
def test_csp_header_includes_provider_hosts(client, provider, expected_hosts):
    providers = {provider: conf_settings.EMBED_PROVIDERS[provider]}
    assert providers[provider]["img_hosts"] == expected_hosts
    csp = _build_csp(providers)
    with override_settings(DEBUG=False, EMBED_PROVIDERS=providers, CONTENT_SECURITY_POLICY=csp):
        resp = client.get("/healthz")
    csp_header = resp["Content-Security-Policy"]
    for host in expected_hosts:
        assert host in csp_header
    assert "'self'" in csp_header
    assert "data:" in csp_header


def test_csp_header_has_img_directive(client):
    csp = {"DIRECTIVES": {"img-src": ("'self'", "data:")}}
    with override_settings(DEBUG=False, CONTENT_SECURITY_POLICY=csp):
        resp = client.get("/healthz")
    csp_header = resp["Content-Security-Policy"]
    assert "img-src" in csp_header
    assert "'self'" in csp_header
    assert "data:" in csp_header


def test_no_legacy_csp_settings():
    assert not hasattr(conf_settings, "CSP_IMG_SRC")


def test_no_legacy_csp_templates():
    from pathlib import Path

    for path in Path("templates").rglob("*.html"):
        text = path.read_text()
        assert "CSP_IMG_SRC" not in text

