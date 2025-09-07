import re
import pytest
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image

from core.models import Community, Post


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=abc123",
        "https://rumble.com/vabcde-example.html",
        "https://x.com/user/status/1",
    ],
)
def test_post_thumbnail_uses_img_not_iframe(url):
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)

    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Video",
        content_url=url,
        image=SimpleUploadedFile(
            "thumb.png",
            (lambda buf: (Image.new("RGB", (1, 1), "white").save(buf, format="PNG"), buf.getvalue()))(BytesIO())[1],
            content_type="image/png",
        ),
    )

    html = render_to_string("partials/post_thumbnail.html", {"post": post})
    assert "<iframe" not in html
    imgs = re.findall(r'<img[^>]+src="([^"]+)"', html)
    assert len(imgs) == 1
    assert imgs[0].startswith(settings.MEDIA_URL)
