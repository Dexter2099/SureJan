import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
import re

from core.models import Community, Post


@pytest.mark.django_db
def test_signup_submit_sort_and_commands(client):
    # signup flow
    r = client.get('/accounts/signup/')
    a, b = client.session['signup_captcha_q']
    r = client.post('/accounts/signup/', {
        'username': 'alice',
        'password': 'pw',
        'captcha': a + b,
    }, follow=True)
    assert r.status_code == 200

    user = get_user_model().objects.get(username='alice')
    client.login(username='alice', password='pw')
    com = Community.objects.create(slug='t', name='Test', title='Test', created_by=user)

    # submit text
    client.post(reverse('post_submit'), {
        'community': com.id,
        'post_type': 'text',
        'title': 'T1',
        'body': 'body',
    }, follow=True)
    # submit link
    client.post(reverse('post_submit'), {
        'community': com.id,
        'post_type': 'link',
        'title': 'L1',
        'content_url': 'https://example.com',
    }, follow=True)
    assert Post.objects.filter(title='T1').exists()
    assert Post.objects.filter(title='L1').exists()

    # sort tab default t=all
    resp = client.get('/?sort=top')
    assert resp.context['t'] == 'all'


    # astro_recompute should exit 0
    call_command('astro_recompute')

    # ensure no external third-party JS before consent
    html = client.get('/').content.decode()
    external_scripts = re.findall(r'src="(http[^"]+)"', html)
    assert external_scripts == []
