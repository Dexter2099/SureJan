import re
from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from PIL import Image

from core.models import Community, Post


@pytest.mark.django_db
def test_post_detail_shows_thumbnail_and_link(client):
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)

    buf = BytesIO()
    Image.new("RGB", (10, 10), "white").save(buf, format="JPEG")
    img = SimpleUploadedFile("a.jpg", buf.getvalue(), content_type="image/jpeg")
    post = Post.objects.create(
        community=com,
        author=user,
        post_type="image",
        title="Img",
        image=img,
        content_url="https://example.com/full.jpg",
    )

    feed_html = client.get("/").content.decode()
    feed_src = re.search(r"<img\s+src=\"([^\"]+)\"", feed_html).group(1)

    detail_html = client.get(post.get_absolute_url()).content.decode()
    detail_match = re.search(r"<img\s+src=\"([^\"]+)\"", detail_html)
    assert detail_match
    detail_src = detail_match.group(1)
    assert detail_src == feed_src
    assert f'href="{post.content_url}"' in detail_html
    assert 'target="_blank"' in detail_html
    assert 'rel="noreferrer noopener"' in detail_html


@pytest.mark.django_db
def test_post_detail_link_placeholder(client):
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)

    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Link",
        content_url="https://example.com/article",
    )

    html = client.get(post.get_absolute_url()).content.decode()
    assert "data:image/svg+xml" in html
    assert f'href="{post.content_url}"' in html
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html
