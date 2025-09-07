import re
from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from PIL import Image

from core.models import Community, Post
from core.utils import thumbnails


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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "link,flag,patch_cache",
    [
        ("https://youtu.be/abc123", "YT_DIRECT_OG", False),
        ("https://rumble.com/v1abc", "RUMBLE_DIRECT_OG", True),
    ],
)
def test_post_detail_rumble_youtube(link, flag, patch_cache, client, settings, monkeypatch, tmp_path):
    cache.clear()
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.MEDIA_URL = "/media/"
    setattr(settings, flag, True)

    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)
    client.login(username="alice", password="pw")

    og_url = "https://img.test/og.jpg"
    buf = BytesIO()
    Image.new("RGB", (1, 1), "white").save(buf, format="PNG")
    img_bytes = buf.getvalue()

    class HtmlResp:
        status_code = 200
        text = f"<meta property='og:image' content='{og_url}'>"
        headers = {}
        content = b""

        def raise_for_status(self):
            pass

    class ImgResp:
        status_code = 200
        headers = {"Content-Type": "image/png"}
        content = img_bytes
        text = ""

        def raise_for_status(self):
            pass

    def fake_fetch_og_html(url, source="og-image", fallback=True):
        if url == og_url:
            return ImgResp()
        return HtmlResp()

    monkeypatch.setattr(thumbnails, "fetch_og_html", fake_fetch_og_html)
    if patch_cache:
        monkeypatch.setattr(thumbnails, "cache_remote_image", lambda u: u)

    resp = client.post(
        reverse("post_submit"),
        {
            "community": com.id,
            "post_type": "link",
            "title": "Link",
            "content_url": link,
        },
        follow=True,
    )
    assert resp.status_code == 200

    post = Post.objects.get(title="Link")
    assert post.image
    assert post.image.url.startswith(settings.MEDIA_URL)

    feed_html = client.get(reverse("home")).content.decode()
    detail_html = client.get(post.get_absolute_url()).content.decode()
    prefix = re.escape(settings.MEDIA_URL)
    assert re.search(f'<img[^>]+src="{prefix}[^\"]+"', feed_html)
    assert re.search(f'<img[^>]+src="{prefix}[^\"]+"', detail_html)


@pytest.mark.django_db
def test_post_detail_og_image_403(client, settings, monkeypatch, tmp_path):
    cache.clear()
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.MEDIA_URL = "/media/"
    settings.YT_DIRECT_OG = True

    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)
    client.login(username="alice", password="pw")

    link = "https://youtu.be/abc123"
    og_url = "https://img.test/og.jpg"

    class HtmlResp:
        status_code = 200
        text = f"<meta property='og:image' content='{og_url}'>"
        headers = {}
        content = b""

        def raise_for_status(self):
            pass

    class ImgResp:
        status_code = 403
        headers = {"Content-Type": "image/jpeg"}
        content = b""
        text = ""

        def raise_for_status(self):
            raise Exception("403")

    def fake_fetch_og_html(url, source="og-image", fallback=True):
        if url == og_url:
            return ImgResp()
        return HtmlResp()

    monkeypatch.setattr(thumbnails, "fetch_og_html", fake_fetch_og_html)

    resp = client.post(
        reverse("post_submit"),
        {
            "community": com.id,
            "post_type": "link",
            "title": "Fail",
            "content_url": link,
        },
        follow=True,
    )
    assert resp.status_code == 200

    post = Post.objects.get(title="Fail")
    assert not post.image

    feed_html = client.get(reverse("home")).content.decode()
    detail_html = client.get(post.get_absolute_url()).content.decode()
    assert "data:image/svg+xml" in feed_html
    assert "data:image/svg+xml" in detail_html
