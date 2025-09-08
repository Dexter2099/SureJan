import importlib


def test_secret_key_fallback(monkeypatch):
    monkeypatch.setenv("DJANGO_DEBUG", "0")
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    monkeypatch.setenv("SECRET_KEY", "fallback")
    from config import settings as conf_settings
    importlib.reload(conf_settings)
    assert conf_settings.SECRET_KEY == "fallback"
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DJANGO_DEBUG", raising=False)
    importlib.reload(conf_settings)

def test_env_allowed_hosts_override(monkeypatch):
    monkeypatch.setenv("DJANGO_DEBUG", "0")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.com")
    from config import settings as conf_settings
    importlib.reload(conf_settings)
    assert conf_settings.ALLOWED_HOSTS == ["example.com"]
    monkeypatch.delenv("DJANGO_ALLOWED_HOSTS", raising=False)
    monkeypatch.delenv("DJANGO_DEBUG", raising=False)
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    importlib.reload(conf_settings)


def test_env_csrf_trusted_override(monkeypatch):
    monkeypatch.setenv("DJANGO_DEBUG", "0")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test")
    monkeypatch.setenv("DJANGO_CSRF_TRUSTED", "https://example.com")
    from config import settings as conf_settings
    importlib.reload(conf_settings)
    assert "https://example.com" in conf_settings.CSRF_TRUSTED_ORIGINS
    monkeypatch.delenv("DJANGO_CSRF_TRUSTED", raising=False)
    monkeypatch.delenv("DJANGO_DEBUG", raising=False)
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    importlib.reload(conf_settings)
