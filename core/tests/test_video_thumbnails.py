import re
import pytest
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.conf import settings

from core.models import Community, Post


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url,thumb_url,expected",
    [
        (
            "https://www.youtube.com/watch?v=abc123",
            "https://i.ytimg.com/thumb.jpg",
            "i.ytimg.com",
        ),
        (
            "https://rumble.com/vabcde-example.html",
            f"{settings.MEDIA_URL}thumb.jpg",
            settings.MEDIA_URL,
        ),
        (
            "https://x.com/user/status/1",
            "https://pbs.twimg.com/thumb.jpg",
            "pbs.twimg.com",
        ),
    ],
)
def test_post_thumbnail_uses_img_not_iframe(url, thumb_url, expected):
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)

    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Video",
        content_url=url,
        thumbnail_url=thumb_url,
    )

    html = render_to_string("partials/post_thumbnail.html", {"post": post})
    assert "<iframe" not in html
    imgs = re.findall(r'<img[^>]+src="([^"]+)"', html)
    assert len(imgs) == 1
    assert expected in imgs[0]
