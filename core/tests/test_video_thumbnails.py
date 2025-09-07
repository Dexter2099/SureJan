import re
import pytest
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.conf import settings

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
        thumbnail_url=f"{settings.MEDIA_URL}thumb.jpg",
    )

    html = render_to_string("partials/post_thumbnail.html", {"post": post})
    assert "<iframe" not in html
    imgs = re.findall(r'<img[^>]+src="([^"]+)"', html)
    assert len(imgs) == 1
    assert imgs[0].startswith(settings.MEDIA_URL)
