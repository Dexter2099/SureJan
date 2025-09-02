import pytest
from django.contrib.auth import get_user_model
from core.models import Community


@pytest.mark.parametrize("path", ["/", "/r/news", "/submit"])
@pytest.mark.django_db
def test_logo_visible_on_core_pages(client, path):
    User = get_user_model()
    user = User.objects.create_user(username="u", password="pw")
    Community.objects.get_or_create(
        slug="news", defaults={"name": "News", "title": "News", "created_by": user}
    )
    if path == "/submit":
        client.login(username="u", password="pw")
    r = client.get(path)
    assert r.status_code in (200, 302)
    html = r.content.decode()
    assert 'class="site-logo"' in html
    assert "/static/logo.png" in html
