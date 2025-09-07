import re
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_htmx_guard_included(client):
    resp = client.get(reverse('home'))
    assert resp.status_code == 200
    html = resp.content.decode()
    assert re.search(r'<script src="/static/js/htmx-guard.*\.js" defer></script>', html)

