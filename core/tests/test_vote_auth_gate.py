import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from urllib.parse import quote

from core.models import Community, Post, Comment


@pytest.fixture
@pytest.mark.django_db

def content():
    User = get_user_model()
    author = User.objects.create_user("author", password="pwd")
    community = Community.objects.create(
        slug="t", name="Test", title="Test", created_by=author
    )
    post = Post.objects.create(
        community=community, author=author, post_type="text", title="Hello"
    )
    comment = Comment.objects.create(post=post, author=author, body="Hi")
    return {"post": post, "comment": comment}


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["post", "comment"])
def test_htmx_requires_login(client, content, kind):
    target = content[kind]
    url = reverse(f"vote_{kind}", args=[target.pk])
    resp = client.post(url, {"v": "1"}, HTTP_HX_REQUEST="true")
    assert resp.status_code == 401
    assert resp.headers["HX-Redirect"] == reverse("login") + f"?next={url}"


@pytest.mark.django_db
def test_htmx_redirect_with_query_string(client, content):
    target = content["post"]
    base_url = reverse("vote_post", args=[target.pk])
    url = base_url + "?foo=bar"
    resp = client.post(url, {"v": "1"}, HTTP_HX_REQUEST="true")
    assert resp.status_code == 401
    expected = reverse("login") + "?next=" + quote(url)
    assert resp.headers["HX-Redirect"] == expected


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["post", "comment"])
def test_normal_post_redirects_to_login(client, content, kind):
    target = content[kind]
    url = reverse(f"vote_{kind}", args=[target.pk])
    resp = client.post(url, {"v": "1"})
    assert resp.status_code == 302
    assert resp["Location"] == reverse("login") + f"?next={url}"


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["post", "comment"])
def test_get_not_allowed(client, content, kind):
    target = content[kind]
    url = reverse(f"vote_{kind}", args=[target.pk])
    resp = client.get(url)
    assert resp.status_code == 405


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["post", "comment"])
def test_logged_in_vote_then_conflict(client, content, kind):
    User = get_user_model()
    voter = User.objects.create_user("voter", password="pwd")
    client.force_login(voter)

    target = content[kind]
    url = reverse(f"vote_{kind}", args=[target.pk])

    resp1 = client.post(url, {"v": "1"})
    assert resp1.status_code == 200
    target.refresh_from_db()
    assert target.score == 1

    resp2 = client.post(url, {"v": "1"})
    assert resp2.status_code == 409
