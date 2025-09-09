import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from urllib.parse import quote

from communities.models import Community
from core.models import Post


@pytest.mark.django_db
def test_login_redirect_preserves_query(client):
    User = get_user_model()
    creator = User.objects.create_user(username="alice", password="pw")
    community = Community.objects.create(slug="t", name="Test", title="Test", created_by=creator)
    post = Post.objects.create(
        community=community,
        author=creator,
        post_type="text",
        title="T1",
        body="body",
    )
    url = reverse("post_detail", args=[community.slug, post.pk, post.slug])
    full_url = f"{url}?foo=bar"

    resp = client.get(full_url)
    assert resp.status_code == 200
    assert f"?next={quote(full_url)}" in resp.content.decode()

    login_url = reverse("login") + f"?next={quote(full_url)}"
    resp = client.post(login_url, {"username": "alice", "password": "pw"}, follow=True)
    assert resp.wsgi_request.get_full_path() == full_url
