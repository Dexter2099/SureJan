import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.conf import settings

from core.models import Community, Post
from core.utils import thumbnails


@pytest.mark.django_db
def test_refetch_thumbs_replaces_remote(monkeypatch):
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

    def fake_resolve(url, label, fetch_remote=False):
        return f"{settings.MEDIA_URL}thumbs/new.jpg", "new"

    monkeypatch.setattr(thumbnails, "resolve_thumbnail", fake_resolve)
    call_command("refetch_thumbs", limit=1)
    post.refresh_from_db()
    assert post.image.url == f"{settings.MEDIA_URL}thumbs/new.jpg"
