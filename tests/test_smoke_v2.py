import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
import os
from django.core.management import call_command
from django.urls import reverse
from django.core.cache import cache
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
    # submit image
    buf = BytesIO()
    Image.new('RGB', (10, 10), 'white').save(buf, format='JPEG')
    img = SimpleUploadedFile('a.jpg', buf.getvalue(), content_type='image/jpeg')
    resp = client.post(reverse('post_submit'), {
        'community': com.id,
        'post_type': 'image',
        'title': 'I1',
        'body': 'caption',
        'image': img,
    }, follow=True)
    assert Post.objects.filter(title='T1').exists()
    assert Post.objects.filter(title='L1').exists()
    assert resp.status_code == 200

    # sort tab default t=all
    resp = client.get('/?sort=top')
    assert resp.context['t'] == 'all'

    # 4MB rejection
    cache.clear()
    prev = Post.objects.count()
    big_buf = BytesIO()
    noise = Image.frombytes('RGB', (2000, 2000), os.urandom(2000 * 2000 * 3))
    noise.save(big_buf, format='PNG')
    big = SimpleUploadedFile('big.png', big_buf.getvalue(), content_type='image/png')
    resp = client.post(reverse('post_submit'), {
        'community': com.id,
        'post_type': 'image',
        'title': 'big',
        'image': big,
    })
    assert resp.status_code == 200
    assert Post.objects.count() == prev

    # astro_recompute should exit 0
    call_command('astro_recompute')

    # ensure no external third-party JS before consent
    html = client.get('/').content.decode()
    external_scripts = re.findall(r'src="(http[^"]+)"', html)
    assert external_scripts == []
