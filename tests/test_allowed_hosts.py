import pytest


@pytest.mark.django_db
@pytest.mark.parametrize("host", [
    "surejan.app",
    "www.surejan.app",
    "foo.fly.dev",
    "127.0.0.1",
])
def test_allowed_hosts_no_disallowed_error(client, settings, host):
    settings.DEBUG = False
    resp = client.get("/", HTTP_HOST=host)
    assert resp.status_code == 200
