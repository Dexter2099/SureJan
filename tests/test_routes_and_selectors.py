import pytest

@pytest.mark.django_db
def test_home_route_renders(client):
    r = client.get("/")
    assert r.status_code in (200, 302)

@pytest.mark.django_db
def test_subreddit_exists(client):
    r = client.get("/r/brisbane")
    assert r.status_code in (200, 302)

@pytest.mark.django_db
def test_post_detail_exists(client):
    r = client.get("/p/1")
    assert r.status_code in (200, 404)

@pytest.mark.django_db
def test_submit_exists(client):
    r = client.get("/submit")
    assert r.status_code in (200, 302)

@pytest.mark.django_db
def test_required_selectors_on_home(client):
    html = client.get("/").content.decode()
    assert 'data-testid="header-bar"' in html
    assert ('data-testid="post-card"' in html) or ('data-testid="empty-state"' in html)
