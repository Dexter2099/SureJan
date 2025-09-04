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
    post, _ = content
    resp = client.get(post.get_absolute_url())
    html = resp.content.decode()
    assert "hx-post" not in html
    assert "Log in to vote" in html


@pytest.mark.django_db
def test_authenticated_shows_vote_buttons(client, content):
    post, comment = content
    User = get_user_model()
    voter = User.objects.create_user("voter", password="pwd")
    client.force_login(voter)
    resp = client.get(post.get_absolute_url())
    html = resp.content.decode()
    assert "hx-post" in html
    assert f'hx-target="#post-score-{post.pk}"' in html
    assert f'hx-target="#comment-score-{comment.pk}"' in html
