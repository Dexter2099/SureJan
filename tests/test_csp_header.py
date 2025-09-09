import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from config import settings as conf_settings
from communities.models import Community
from core.models import Post


@pytest.mark.django_db
def test_csp_headers_include_expected_hosts(client):
    User = get_user_model()
    user = User.objects.create_user("author", password="pw")
    community = Community.objects.create(
        slug="test", name="Test", title="Test", created_by=user
    )
    post = Post.objects.create(
        community=community,
        author=user,
        post_type="link",
        title="Video",
        content_url="https://www.youtube.com/watch?v=abc",
    )
    urls = [
        "/",
        "/healthz",
        reverse("post_detail", args=[community.slug, post.pk, post.slug]),
    ]
    expected_hosts = [
        "'self'",
        "data:",
        "https://surejan-media.fly.storage.tigris.dev",
    ]
    csp = {"DIRECTIVES": {"img-src": tuple(expected_hosts)}}
    with override_settings(DEBUG=False, CONTENT_SECURITY_POLICY=csp):
        for url in urls:
            resp = client.get(url)
            csp_header = resp["Content-Security-Policy"]
            assert "img-src" in csp_header
            for host in expected_hosts:
                assert host in csp_header


def test_no_legacy_csp_settings():
    assert not hasattr(conf_settings, "CSP_IMG_SRC")


def test_no_legacy_csp_templates():
    from pathlib import Path

    for path in Path("templates").rglob("*.html"):
        text = path.read_text()
        assert "CSP_IMG_SRC" not in text

