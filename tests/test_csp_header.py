import pytest
from django.test import override_settings
from config import settings as conf_settings


def test_csp_header_includes_img_src_hosts(client):
    csp = {
        "DIRECTIVES": {
            "img-src": tuple(
                ["'self'", "https:"] + conf_settings._csp_img_src + ["data:"]
            )
        }
    }
    with override_settings(DEBUG=False, CONTENT_SECURITY_POLICY=csp):
        resp = client.get("/healthz")
    csp_header = resp["Content-Security-Policy"]
    for host in conf_settings._csp_img_src:
        assert host in csp_header


def test_csp_header_includes_frame_src_hosts(client):
    csp = {
        "DIRECTIVES": {
            "frame-src": tuple(["'self'"] + conf_settings._csp_frame_src)
        }
    }
    with override_settings(DEBUG=False, CONTENT_SECURITY_POLICY=csp):
        resp = client.get("/healthz")
    csp_header = resp["Content-Security-Policy"]
    for host in conf_settings._csp_frame_src:
        assert host in csp_header
