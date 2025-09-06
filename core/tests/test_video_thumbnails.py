import re
import pytest
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from core.models import Community, Post


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url,thumb_host",
    [
        ("https://www.youtube.com/watch?v=abc123", "i.ytimg.com"),
        ("https://rumble.com/vabcde-example.html", "rumblecdn.com"),
        ("https://x.com/user/status/1", "pbs.twimg.com"),
    ],
)
def test_post_thumbnail_uses_img_not_iframe(url, thumb_host):
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)

    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Video",
        content_url=url,
        thumbnail_url=f"https://{thumb_host}/thumb.jpg",
    )

    html = render_to_string("partials/post_thumbnail.html", {"post": post})
    assert "<iframe" not in html
    imgs = re.findall(r'<img[^>]+src="([^"]+)"', html)
    assert len(imgs) == 1
    assert thumb_host in imgs[0]
