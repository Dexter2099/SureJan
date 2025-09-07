import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from core.models import Community, Post


@pytest.mark.django_db
def test_convert_rumble_thumbs(monkeypatch):
    User = get_user_model()
    user = User.objects.create_user("alice", password="pw")
    com = Community.objects.create(slug="t", name="Test", title="Test", created_by=user)
    post = Post.objects.create(
        community=com,
        author=user,
        post_type="link",
        title="Link",
        content_url="https://rumble.com/v1abc",
    )
    Post.objects.filter(pk=post.pk).update(image="https://sp.rmbl.ws/s8/1/v1abc.jpg")
    post.refresh_from_db()

    from core.management.commands import convert_rumble_thumbs

    def fake_cache(origin_url):
        return "/media/thumbs/rumble/cache.jpg"

    monkeypatch.setattr(convert_rumble_thumbs, "cache_remote_image", fake_cache)
    call_command("convert_rumble_thumbs")
    post.refresh_from_db()
    assert post.image.url == "/media/thumbs/rumble/cache.jpg"

    Post.objects.filter(pk=post.pk).update(image="https://sp.rmbl.ws/s8/1/v1abc.jpg")
    post.refresh_from_db()
    calls: list[str] = []

    def fake_cache2(origin_url):
        calls.append(origin_url)
        return "/media/thumbs/rumble/cache2.jpg"

    monkeypatch.setattr(convert_rumble_thumbs, "cache_remote_image", fake_cache2)
    call_command("convert_rumble_thumbs", dry_run=True)
    post.refresh_from_db()
    assert post.image.name == "https://sp.rmbl.ws/s8/1/v1abc.jpg"
    assert calls == ["https://sp.rmbl.ws/s8/1/v1abc.jpg"]
