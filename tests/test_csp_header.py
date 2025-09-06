import pytest
from django.test import override_settings

from config import settings as conf_settings


def _build_csp(providers):
    img_src = ["'self'"]
    frame_src = ["'self'"]
    for p in providers.values():
        if p["flag"]:
            img_src.extend(p["img_hosts"])
            frame_src.extend(p["frame_hosts"])
    img_src.append("data:")
    return {"DIRECTIVES": {"img-src": tuple(img_src), "frame-src": tuple(frame_src)}}


@pytest.mark.parametrize("provider", ["YOUTUBE", "X", "RUMBLE"])
def test_csp_header_includes_provider_hosts(client, provider):
    providers = {k: v.copy() for k, v in conf_settings.EMBED_PROVIDERS.items()}
    for p in providers.values():
        p["flag"] = False
    providers[provider]["flag"] = True
    csp = _build_csp(providers)
    with override_settings(DEBUG=False, EMBED_PROVIDERS=providers, CONTENT_SECURITY_POLICY=csp):
        resp = client.get("/healthz")
    csp_header = resp["Content-Security-Policy"]
    for host in providers[provider]["img_hosts"] + providers[provider]["frame_hosts"]:
        assert host in csp_header


def test_no_legacy_csp_settings():
    assert not hasattr(conf_settings, "CSP_IMG_SRC")
    assert not hasattr(conf_settings, "CSP_FRAME_SRC")
