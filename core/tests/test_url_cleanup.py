from core.utils.url_cleanup import cleanup_url


def test_cleanup_strips_tracking_params():
    url = "https://example.com/watch?v=1&utm_source=newsletter&fbclid=123&x=1"
    assert cleanup_url(url) == "https://example.com/watch?v=1&x=1"


def test_cleanup_rumble_drops_all_queries():
    url = "https://rumble.com/v1abcd-something.html?foo=bar&utm_source=newsletter"
    assert cleanup_url(url) == "https://rumble.com/v1abcd-something.html"


def test_cleanup_uses_canonicalize():
    url = "https://youtu.be/abc123?utm_source=foo"
    assert cleanup_url(url) == "https://youtube.com/watch?v=abc123"
