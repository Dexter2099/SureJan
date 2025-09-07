import re
import pytest
from django.urls import reverse
from django.utils.html import escape
from django.contrib.auth import get_user_model

from core.models import Community, Post


@pytest.mark.django_db
def test_link_post_shows_plain_content_url(client):
    User = get_user_model()
    user = User.objects.create_user(username="alice", password="pw")
    community = Community.objects.create(
        slug="test",
        name="test",
        title="Test",
        created_by=user,
    )
    url = "https://example.com/path?q=1&x=<tag>"
    post = Post.objects.create(
        community=community,
        author=user,
        post_type="link",
        title="Link post",
        content_url=url,
    )

    resp = client.get(reverse("post_detail", args=[community.slug, post.pk, post.slug]))
    assert resp.status_code == 200
    html = resp.content.decode()

    # shows escaped, non-linked URL
    assert f"from: {escape(url)}" in html
    assert url not in html  # raw URL should be escaped

    # preview elements removed
    article = re.search(r'<article[^>]*class="post-detail"[^>]*>(.*?)</article>', html, re.DOTALL).group(1)
    assert "<img" not in article
    assert "<iframe" not in article
