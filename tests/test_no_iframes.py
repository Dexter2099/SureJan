import re
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
        html = resp.content.decode().lower()
        iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', html)
        allowed = (
            "youtube.com/embed/",
            "rumble.com/embed/",
            "platform.twitter.com/embed/tweet.html",
        )
        for src in iframes:
            assert any(a in src for a in allowed)
