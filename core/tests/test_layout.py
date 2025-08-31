import pytest


@pytest.mark.django_db
def test_homepage_layout(client):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.content.decode()
    assert '<main class="layout">' in html
    assert '<section class="main feed">' in html
    assert '<aside class="sidebar">' in html


@pytest.mark.django_db
def test_anti_astroturf_bullets(client):
    resp = client.get("/anti-astroturf/")
    assert resp.status_code == 200
    html = resp.content.decode()
    assert "No undisclosed paid promotions or campaigns." in html
    assert "No vote manipulation or brigading." in html
    assert "Organizations and officials must identify themselves." in html
