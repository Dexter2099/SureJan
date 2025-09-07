import pytest
from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image

from core.models import Community, Post


@pytest.mark.django_db
def test_thumbnail_click_map(client):
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)
    buf = BytesIO()
    Image.new("RGB", (1, 1), "white").save(buf, format="PNG")
    thumb_file = SimpleUploadedFile("thumb.png", buf.getvalue(), content_type="image/png")
    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Link",
        content_url="https://example.com/article",
        image=thumb_file,
    )
    Post.objects.filter(pk=post.pk).update(image_thumb=None)
    post.refresh_from_db()

    # Feed page
    html = client.get("/").content.decode()
    soup = BeautifulSoup(html, "html.parser")
    card = soup.select_one("article.post-card")
    title_a = card.select_one("h3.post-title a")
    assert title_a["href"] == post.get_absolute_url()
    thumb_a = card.select_one("a.thumb")
    assert thumb_a["href"] == post.content_url
    assert thumb_a["target"] == "_blank"
    assert set(thumb_a["rel"]) == {"noopener", "noreferrer"}

    # Detail page
    html = client.get(post.get_absolute_url()).content.decode()
    soup = BeautifulSoup(html, "html.parser")
    thumb_a = soup.select_one("article.post-detail a.thumb")
    assert thumb_a["href"] == post.content_url
    assert thumb_a["target"] == "_blank"
    assert set(thumb_a["rel"]) == {"noopener", "noreferrer"}
