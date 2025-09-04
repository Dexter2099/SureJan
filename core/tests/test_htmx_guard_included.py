import pytest
from django.urls import reverse
from django.test import override_settings


@pytest.mark.django_db
@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage",
    STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}},
)
def test_htmx_guard_included(client):
    resp = client.get(reverse('home'))
    assert resp.status_code == 200
    html = resp.content.decode()
    assert '<script src="/static/js/htmx-guard.js" defer></script>' in html

