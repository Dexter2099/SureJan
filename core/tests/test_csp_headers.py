import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from config import settings as conf_settings
from core.models import Community, Post


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
        reverse("post_detail", args=[community.slug, post.pk, post.slug]),
    ]
    csp = {
        "DIRECTIVES": {
            "img-src": tuple(
                ["'self'", "https:"] + conf_settings._csp_img_src + ["data:"]
            ),
            "frame-src": tuple(["'self'"] + conf_settings._csp_frame_src),
        }
    }
    with override_settings(DEBUG=False, CONTENT_SECURITY_POLICY=csp):
        for url in urls:
            resp = client.get(url)
            csp_header = resp["Content-Security-Policy"]
            for host in conf_settings._csp_img_src:
                assert host in csp_header
            for host in conf_settings._csp_frame_src:
                assert host in csp_header
