import pytest
from django.contrib.auth import get_user_model

from core.models import Community, Post


@pytest.mark.django_db
def test_no_iframes_in_rendered_pages(client):
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)
    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Link",
        content_url="https://example.com",
        thumbnail_url="https://example.com/thumb.jpg",
    )

    urls = ["/", post.get_absolute_url()]
    for url in urls:
        html = client.get(url).content.decode()
        assert "<iframe" not in html
