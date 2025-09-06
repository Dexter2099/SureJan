import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_homepage_layout(client):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.content.decode()
    assert 'class="layout' in html
    assert 'feed-col' in html


@pytest.mark.django_db
def test_anti_astroturf_bullets(client):
    url = reverse("transparency_methods")
    resp = client.get(url)
    assert resp.status_code == 200
    html = resp.content.decode()
    assert "No undisclosed paid promotions or campaigns." in html
    assert "No vote manipulation or brigading." in html
    assert "Organizations and officials must identify themselves." in html
