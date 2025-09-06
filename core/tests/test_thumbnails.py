from unittest.mock import patch
import os
from django.core.cache import cache
from core.utils import thumbnails


def test_resolve_thumbnail_oembed_first():
    with patch('core.utils.thumbnails.fetch_oembed', return_value={'thumbnail_url': 'http://a/b.jpg'}), \
         patch('core.utils.thumbnails.fetch_og_image') as mock_og:
        src, alt = thumbnails.resolve_thumbnail('https://example.com', 'Preview')
    assert src == 'https://a/b.jpg'
    assert alt == 'Preview'
    mock_og.assert_not_called()


def test_resolve_thumbnail_provider_default():
    with patch('core.utils.thumbnails.fetch_oembed', return_value={}), \
         patch('core.utils.thumbnails.fetch_og_image', return_value=None):
        src, alt = thumbnails.resolve_thumbnail('https://www.youtube.com/watch?v=abc123', 'Preview')
    assert src == 'https://i.ytimg.com/vi/abc123/hqdefault.jpg'
    assert alt == 'Preview'


def test_resolve_thumbnail_og_image():
    with patch('core.utils.thumbnails.fetch_oembed', return_value={}), \
         patch('core.utils.thumbnails.fetch_og_image', return_value='http://cdn.example/img.jpg'):
        src, alt = thumbnails.resolve_thumbnail('https://example.com/post', 'Preview')
    assert src == 'https://cdn.example/img.jpg'
    assert alt == 'Preview'


def test_resolve_thumbnail_fallback():
    with patch('core.utils.thumbnails.fetch_oembed', return_value={}), \
         patch('core.utils.thumbnails.fetch_og_image', return_value=None):
        src, alt = thumbnails.resolve_thumbnail('https://example.com', 'Preview')
    assert src.startswith('data:image/svg+xml')
    assert alt == 'Preview image unavailable'


def test_fetch_og_image_caches_success():
    url = 'https://example.com'
    cache.clear()
    with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": ""}):
        with patch('core.utils.thumbnails.scrape_og_image', return_value=('https://cdn.example/img.jpg', 200)) as mock_scrape:
            assert thumbnails.fetch_og_image(url) == 'https://cdn.example/img.jpg'
            assert thumbnails.fetch_og_image(url) == 'https://cdn.example/img.jpg'
    assert mock_scrape.call_count == 1


def test_fetch_og_image_no_cache_on_error():
    url = 'https://example.com'
    cache.clear()
    with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": ""}):
        with patch('core.utils.thumbnails.scrape_og_image', return_value=(None, 500)) as mock_scrape:
            assert thumbnails.fetch_og_image(url) is None
            assert thumbnails.fetch_og_image(url) is None
    assert mock_scrape.call_count == 2
