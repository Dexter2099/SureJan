import pytest

from core.utils.video_urls import (
    canonicalize_youtube,
    canonicalize_rumble_url,
    canonicalize_x,
    canonicalize_video_url,
)


def test_canonicalize_youtube_variants():
    urls = [
        "https://www.youtube.com/watch?v=abc123&t=1s",
        "https://youtu.be/abc123?si=xyz",
        "https://youtube.com/embed/abc123",
        "https://youtube.com/shorts/abc123?feature=share",
    ]
    for u in urls:
        assert canonicalize_youtube(u) == "https://youtube.com/watch?v=abc123"


def test_canonicalize_rumble_variants():
    assert (
        canonicalize_rumble_url("https://rumble.com/v1abcd-something.html?foo=bar")
        == "https://rumble.com/v1abcd-something.html"
    )
    assert (
        canonicalize_rumble_url("https://rumble.com/embed/v1abcd?pub=123")
        == "https://rumble.com/v1abcd.html"
    )


def test_canonicalize_x_variants():
    urls = [
        "https://twitter.com/user/status/123?s=20",
        "https://x.com/user/status/123?lang=en",
        "https://fxtwitter.com/user/status/123",
    ]
    for u in urls:
        assert canonicalize_x(u) == "https://x.com/user/status/123"


def test_canonicalize_video_url_dispatcher():
    assert (
        canonicalize_video_url("https://youtu.be/abc123")
        == "https://youtube.com/watch?v=abc123"
    )
    assert (
        canonicalize_video_url("https://rumble.com/embed/v1abcd")
        == "https://rumble.com/v1abcd.html"
    )
    assert (
        canonicalize_video_url("https://twitter.com/user/status/123")
        == "https://x.com/user/status/123"
    )
    assert (
        canonicalize_video_url("https://example.com/foo")
        == "https://example.com/foo"
    )
