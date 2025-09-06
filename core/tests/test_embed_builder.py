from core.utils.embed_builder import build_embed_iframe

def test_build_embed_iframe_youtube():
    html = build_embed_iframe("https://youtu.be/abc123")
    assert html and "https://www.youtube.com/embed/abc123" in html

def test_build_embed_iframe_rumble():
    html = build_embed_iframe("https://rumble.com/v1abcd")
    assert html and "https://rumble.com/embed/v1abcd" in html

def test_build_embed_iframe_x():
    html = build_embed_iframe("https://twitter.com/user/status/123")
    assert html and "https://platform.twitter.com/embed/Tweet.html?id=123" in html

def test_build_embed_iframe_unknown():
    assert build_embed_iframe("https://example.com/video") is None
