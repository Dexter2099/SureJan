import pytest
from django.urls import reverse

from communities.models import Community
from core.models import Post


@pytest.fixture
def post(db, django_user_model):
    author = django_user_model.objects.create_user("author", password="pw")
    community = Community.objects.create(slug="t", name="Test", title="Test", created_by=author)
    return Post.objects.create(community=community, author=author, post_type="text", title="Hello")


@pytest.mark.django_db
def test_vote_is_immutable_and_buttons_disabled(client, django_user_model, post):
    user = django_user_model.objects.create_user(username="u1", password="pw")
    client.login(username="u1", password="pw")

    url = reverse("vote_post", args=[post.id])

    r1 = client.post(url, {"v": "1"}, HTTP_HX_REQUEST="true")
    assert r1.status_code == 200
    body = r1.content.decode()
    assert f'id="post-{post.id}-score"' in body
    assert "disabled" in body

    r2 = client.post(url, {"v": "1"}, HTTP_HX_REQUEST="true")
    assert r2.status_code == 409
