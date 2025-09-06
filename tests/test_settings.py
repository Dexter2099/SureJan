import importlib


def test_twimg_in_csp_by_default(monkeypatch):
    monkeypatch.setenv("DJANGO_DEBUG", "0")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test")
    from config import settings as conf_settings
    importlib.reload(conf_settings)
    img_src = conf_settings.CONTENT_SECURITY_POLICY["DIRECTIVES"]["img-src"]
    assert any("twimg.com" in h for h in img_src)
    monkeypatch.delenv("DJANGO_DEBUG", raising=False)
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    importlib.reload(conf_settings)
