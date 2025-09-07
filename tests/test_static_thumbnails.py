import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image

from core.models import Community, Post


@pytest.mark.django_db
def test_feed_and_detail_render_thumbnails(client):
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)
    buf = BytesIO()
    Image.new("RGB", (1, 1), "white").save(buf, format="PNG")
    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Link",
        content_url="https://example.com",
        image=SimpleUploadedFile("thumb.png", buf.getvalue(), content_type="image/png"),
    )
    Post.objects.filter(pk=post.pk).update(image_thumb=None)
    post.refresh_from_db()

    for url in ["/", post.get_absolute_url()]:
        html = client.get(url).content.decode()
        assert f'src="{post.image.url}"' in html
