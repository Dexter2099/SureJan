import pytest

@pytest.mark.django_db
@pytest.mark.parametrize("path", ["/", "/r/news", "/r/brisbane"])
def test_core_pages_render(client, path):
    r = client.get(path)
    assert r.status_code in (200, 302)

@pytest.mark.django_db
def test_header_and_tabs(client):
    html = client.get("/").content.decode()
    assert 'data-testid="header-bar"' in html
    assert 'id="sort-tabs"' in html

@pytest.mark.django_db
def test_submit_present(client):
    html = client.get("/").content.decode()
    assert 'data-testid="sidebar-submit"' in html

@pytest.mark.django_db
def test_top_time_rules(client):
    assert client.get("/?sort=top").status_code in (200, 302)
    assert client.get("/?sort=top&t=24h").status_code in (200, 302)
