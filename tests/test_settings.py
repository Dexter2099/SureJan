import importlib


def test_twimg_in_csp_when_twitter_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_TWITTER_EMBEDS", "1")
    from config import settings as conf_settings
    importlib.reload(conf_settings)
    assert any("twimg.com" in h for h in conf_settings.CSP_IMG_SRC)
    monkeypatch.delenv("ENABLE_TWITTER_EMBEDS", raising=False)
    importlib.reload(conf_settings)
