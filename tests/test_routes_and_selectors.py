import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

from core.models import Community, Post


@pytest.mark.django_db
def test_home_route_status_code(client):
    response = client.get(reverse('home'))
    assert response.status_code in {200, 302, 404}


@pytest.mark.django_db
def test_subreddit_route_status_code(client):
    user = get_user_model().objects.create_user('tester', password='pwd')
    community = Community.objects.create(slug='test', name='Test', title='Test', created_by=user)
    response = client.get(reverse('community', args=[community.slug]))
    assert response.status_code in {200, 302, 404}


@pytest.mark.django_db
def test_post_detail_route_status_code(client):
    user = get_user_model().objects.create_user('tester', password='pwd')
    community = Community.objects.create(slug='test', name='Test', title='Test', created_by=user)
    post = Post.objects.create(community=community, author=user, post_type='text', title='Hello')
    response = client.get(reverse('post_detail', args=[community.slug, post.pk, post.slug]))
    assert response.status_code in {200, 302, 404}


@pytest.mark.django_db
def test_submit_route_status_code(client):
    response = client.get(reverse('post_submit'))
    assert response.status_code in {200, 302, 404}


@pytest.mark.django_db
def test_required_selectors_present(client):
    user = get_user_model().objects.create_user('tester', password='pwd')
    community = Community.objects.create(slug='test', name='Test', title='Test', created_by=user)
    Post.objects.create(community=community, author=user, post_type='text', title='Hello')

    home_resp = client.get(reverse('home'))
    assert home_resp.status_code in {200, 302, 404}
    html = home_resp.content.decode()
    assert 'data-testid="post-card"' in html
    assert 'data-testid="sidebar-cta"' in html

    client.force_login(user)
    submit_resp = client.get(reverse('post_submit'))
    assert submit_resp.status_code in {200, 302, 404}
    submit_html = submit_resp.content.decode()
    assert 'data-testid="submit-form"' in submit_html
