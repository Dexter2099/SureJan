import pytest
from django.contrib.auth import get_user_model

from core.models import Community, Post


@pytest.mark.django_db
def test_feed_and_detail_render_thumbnails(client):
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)
    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Link",
        content_url="https://example.com",
    )
    Post.objects.filter(pk=post.pk).update(image="thumb.jpg", image_thumb="thumb.jpg")
    post.refresh_from_db()

    for url in ["/", post.get_absolute_url()]:
        html = client.get(url).content.decode()
        assert "<img" in html
