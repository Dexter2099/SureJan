import re
from io import BytesIO

import pytest
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
    img_post = Post.objects.create(
        community=com,
        author=user,
        post_type="image",
        title="Img",
        image=img,
    )

    # Link post with explicit thumbnail
    thumb_data = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00"
        b"\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    link_post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Link",
        content_url="https://example.com",
        image_thumb=SimpleUploadedFile("thumb.png", thumb_data, content_type="image/png"),
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
    img_post.refresh_from_db()
    link_post.refresh_from_db()
    cards = re.findall(
        r"<article[^>]*data-testid=\"post-card\"[^>]*>(.*?)</article>", html, re.DOTALL
    )
    assert len(cards) == 3
    imgs = re.findall(r'<img[^>]+src="([^"]+)"', html)
    img_src = img_post.image_thumb.url if img_post.image_thumb else img_post.image.url
    assert img_src in imgs
    assert link_post.image_thumb.url in imgs
    assert any(src.startswith("data:image/svg+xml") for src in imgs)
