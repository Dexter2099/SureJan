import pytest
from django.contrib.auth import get_user_model

from core.models import Community, Post, Comment


@pytest.fixture
def content(db):
    User = get_user_model()
    author = User.objects.create_user("author", password="pwd")
    community = Community.objects.create(
        slug="t", name="Test", title="Test", created_by=author
    )
    post = Post.objects.create(
        community=community, author=author, post_type="text", title="Hello"
    )
    comment = Comment.objects.create(post=post, author=author, body="Hi")
    return post, comment


@pytest.mark.django_db
def test_anonymous_shows_login_prompt(client, content):
    post, comment = content
    resp = client.get(post.get_absolute_url())
    html = resp.content.decode()
    assert "hx-post" not in html
    assert "Log in to vote" in html
    assert f'id="post-{post.pk}-score"' in html
    assert f'id="comment-{comment.pk}-score"' in html


@pytest.mark.django_db
def test_authenticated_shows_vote_buttons(client, content):
    post, comment = content
    User = get_user_model()
    voter = User.objects.create_user("voter", password="pwd")
    client.force_login(voter)
    resp = client.get(post.get_absolute_url())
    html = resp.content.decode()
    assert "hx-post" in html
    assert f'hx-target="#post-{post.pk}-vote"' in html
    assert f'hx-target="#comment-{comment.pk}-vote"' in html


@pytest.mark.django_db
def test_vote_widget_hx_on_only_disables_on_200(client, content):
    post, comment = content
    User = get_user_model()
    voter = User.objects.create_user("voter", password="pwd")
    client.force_login(voter)
    resp = client.get(post.get_absolute_url())
    html = resp.content.decode()
    assert f'id="post-{post.pk}-vote"' in html
    assert f'id="comment-{comment.pk}-vote"' in html
    assert "hx-on::after-swap=\"if(event.detail.xhr.status===200)" in html
