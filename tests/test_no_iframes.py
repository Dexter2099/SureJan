import pytest
from django.contrib.auth import get_user_model

from core.models import Community


@pytest.mark.django_db
def test_no_iframes(client):
    User = get_user_model()
    creator = User.objects.create_user(username="alice", password="pw")
    community = Community.objects.create(slug="t", name="Test", title="Test", created_by=creator)

    urls = [
        "/",
        f"/r/{community.slug}/",
    ]

    for url in urls:
        resp = client.get(url)
        assert resp.status_code == 200
        assert "<iframe" not in resp.content.decode().lower()
