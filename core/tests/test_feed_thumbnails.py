import re
from io import BytesIO

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from PIL import Image

from core.models import Community, Post


@pytest.mark.django_db
def test_feed_thumbnails_are_images(client):
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)

    # Image post with uploaded picture
    buf = BytesIO()
    Image.new("RGB", (10, 10), "white").save(buf, format="JPEG")
    img = SimpleUploadedFile("a.jpg", buf.getvalue(), content_type="image/jpeg")
    Post.objects.create(
        community=com,
        author=user,
        post_type="image",
        title="Img",
        image=img,
    )

    # Link post with explicit thumbnail
    Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Link",
        content_url="https://example.com",
        thumbnail_url=f"{settings.MEDIA_URL}thumb.jpg",
    )

    # Link post without thumbnail should use placeholder
    Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="NoThumb",
        content_url="https://example.com/article",
    )

    resp = client.get("/")
    html = resp.content.decode()
    cards = re.findall(
        r"<article[^>]*data-testid=\"post-card\"[^>]*>(.*?)</article>", html, re.DOTALL
    )
    assert len(cards) == 3
    for card in cards:
        assert "<img" in card
    assert "data:image/svg+xml" in html
