from unittest.mock import patch, Mock
from urllib.parse import urlparse

import requests

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from config import settings as conf_settings
from core.models import Community, Post, PostImageLink


class PostDetailMediaTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("author", password="pw")
        self.community = Community.objects.create(
            slug="test", name="Test", title="Test", created_by=self.user
        )

    @override_settings(ENABLE_YOUTUBE_EMBEDS=True)
    @patch("core.utils.thumbnails.fetch_oembed")
    @patch("core.utils.embeds.fetch_oembed")
    def test_youtube_embed_has_placeholder(self, mock_embed_oembed, mock_thumb_oembed):
        mock_embed_oembed.return_value = {
            "type": "embed",
            "html": '<iframe src="https://www.youtube.com/embed/abc"></iframe>',
            "thumbnail_url": "http://img.youtube.com/vi/abc/hqdefault.jpg",
        }
        mock_thumb_oembed.return_value = mock_embed_oembed.return_value
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Video",
            content_url="https://www.youtube.com/watch?v=abc",
        )
        resp = self.client.get(
            reverse("post_detail", args=[self.community.slug, post.pk, post.slug])
        )
        self.assertContains(resp, 'data-src="https://www.youtube-nocookie.com/embed/abc"')
        self.assertContains(resp, 'href="https://www.youtube.com/watch?v=abc"')
        self.assertContains(
            resp, 'src="https://img.youtube.com/vi/abc/hqdefault.jpg"'
        )

    @override_settings(ENABLE_YOUTUBE_EMBEDS=True)
    @patch("core.utils.thumbnails._provider_default", return_value=None)
    @patch("core.utils.thumbnails.fetch_oembed")
    @patch("core.utils.thumbnails.fetch_og_image")
    @patch("core.utils.embeds.fetch_oembed")
    def test_embed_uses_og_image_when_no_thumbnail(
        self, mock_embed_oembed, mock_fetch_og_image, mock_thumb_oembed, mock_provider_default
    ):
        mock_embed_oembed.return_value = {
            "type": "embed",
            "html": '<iframe src="https://www.youtube.com/embed/abc"></iframe>',
            "thumbnail_url": None,
        }
        mock_thumb_oembed.return_value = mock_embed_oembed.return_value
        mock_fetch_og_image.return_value = "https://cdn.example/og.jpg"
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Video OG",
            content_url="https://www.youtube.com/watch?v=abc",
        )
        resp = self.client.get(
            reverse("post_detail", args=[self.community.slug, post.pk, post.slug])
        )
        self.assertContains(resp, 'src="https://cdn.example/og.jpg"')

    @override_settings(ENABLE_RUMBLE_EMBEDS=True)
    @patch("core.utils.thumbnails.fetch_og_image", return_value=None)
    @patch("core.utils.thumbnails.fetch_oembed")
    @patch("core.utils.embeds.fetch_oembed")
    def test_embed_uses_placeholder_when_og_fetch_fails(
        self, mock_embed_oembed, mock_thumb_oembed, mock_fetch_og_image
    ):
        mock_embed_oembed.return_value = {
            "type": "embed",
            "html": '<iframe src="https://rumble.com/embed/vxyz/"></iframe>',
            "thumbnail_url": None,
        }
        mock_thumb_oembed.return_value = mock_embed_oembed.return_value
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Rumble 403",
            content_url="https://rumble.com/vxyz-test.html",
        )
        resp = self.client.get(
            reverse("post_detail", args=[self.community.slug, post.pk, post.slug])
        )
        self.assertContains(resp, 'src="data:image/svg+xml;utf8,')

    @override_settings(ENABLE_YOUTUBE_EMBEDS=True)
    @patch("core.utils.thumbnails._provider_default", return_value=None)
    @patch("core.utils.thumbnails.fetch_oembed")
    @patch("core.utils.thumbnails.fetch_og_image", return_value="https://cdn.example/og2.jpg")
    @patch("core.utils.embeds.fetch_oembed")
    def test_embed_uses_scraped_og_image_when_available(
        self, mock_embed_oembed, mock_fetch_og_image, mock_thumb_oembed, mock_provider_default
    ):
        mock_embed_oembed.return_value = {
            "type": "embed",
            "html": '<iframe src="https://www.youtube.com/embed/abc"></iframe>',
            "thumbnail_url": None,
        }
        mock_thumb_oembed.return_value = mock_embed_oembed.return_value
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Video OG2",
            content_url="https://www.youtube.com/watch?v=abc",
        )
        resp = self.client.get(
            reverse("post_detail", args=[self.community.slug, post.pk, post.slug])
        )
        self.assertContains(resp, 'src="https://cdn.example/og2.jpg"')

    @override_settings(ENABLE_RUMBLE_EMBEDS=True)
    @patch("core.utils.thumbnails.fetch_oembed")
    @patch("core.utils.embeds.fetch_oembed")
    def test_rumble_embed_has_placeholder(self, mock_embed_oembed, mock_thumb_oembed):
        mock_embed_oembed.return_value = {
            "type": "embed",
            "html": '<iframe src="https://rumble.com/embed/vxyz/?pub=4"></iframe>',
            "thumbnail_url": "http://thumb.jpg",
        }
        mock_thumb_oembed.return_value = mock_embed_oembed.return_value
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Rumble",
            content_url="https://rumble.com/vxyz-test.html",
        )
        resp = self.client.get(
            reverse("post_detail", args=[self.community.slug, post.pk, post.slug])
        )
        self.assertContains(resp, 'data-src="https://rumble.com/embed/vxyz/?pub=4"')
        self.assertContains(resp, 'href="https://rumble.com/vxyz-test.html"')
        self.assertContains(resp, 'src="https://thumb.jpg"')

    @override_settings(ENABLE_RUMBLE_EMBEDS=True)
    @patch("core.utils.thumbnails.fetch_og_image", return_value=None)
    @patch("core.utils.thumbnails.fetch_oembed")
    @patch("core.utils.embeds.fetch_oembed")
    def test_rumble_embed_handles_single_quotes_in_iframe(
        self, mock_embed_oembed, mock_thumb_oembed, mock_fetch_og_image
    ):
        mock_embed_oembed.return_value = {
            "type": "embed",
            "html": "<iframe src='https://rumble.com/embed/vxyz/?pub=4'></iframe>",
            "thumbnail_url": None,
        }
        mock_thumb_oembed.return_value = mock_embed_oembed.return_value
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Rumble SQ",
            content_url="https://rumble.com/vxyz-test.html",
        )
        resp = self.client.get(
            reverse("post_detail", args=[self.community.slug, post.pk, post.slug])
        )
        self.assertContains(resp, 'data-src="https://rumble.com/embed/vxyz/?pub=4"')
        self.assertContains(resp, 'href="https://rumble.com/vxyz-test.html"')
        # With missing thumbnail_url, we should still render an <img> (data: URL fallback)
        self.assertContains(resp, 'src="data:image/svg+xml;utf8,')

    @override_settings(ENABLE_RUMBLE_EMBEDS=True)
    @patch("core.utils.thumbnails.fetch_og_image", return_value=None)
    @patch("core.utils.thumbnails.fetch_oembed")
    @patch("core.utils.embeds.fetch_oembed")
    def test_rumble_embed_falls_back_when_no_iframe_html(
        self, mock_embed_oembed, mock_thumb_oembed, mock_fetch_og_image
    ):
        # oEmbed returns no iframe; builder derives /embed/<id>/ from page URL /vxyz-...
        mock_embed_oembed.return_value = {
            "type": "embed",
            "html": "<div>no iframe here</div>",
            "thumbnail_url": None,
        }
        mock_thumb_oembed.return_value = mock_embed_oembed.return_value
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Rumble Fallback",
            content_url="https://rumble.com/vxyz-interesting-video.html",
        )
        resp = self.client.get(
            reverse("post_detail", args=[self.community.slug, post.pk, post.slug])
        )
        self.assertContains(resp, 'data-src="https://rumble.com/embed/vxyz/"')
        self.assertContains(resp, 'href="https://rumble.com/vxyz-interesting-video.html"')
        self.assertContains(resp, 'src="data:image/svg+xml;utf8,')

    @override_settings(ENABLE_TWITTER_EMBEDS=True)
    @patch("core.utils.thumbnails.fetch_oembed")
    @patch("core.utils.embeds.fetch_oembed")
    def test_twitter_embed_has_placeholder(self, mock_embed_oembed, mock_thumb_oembed):
        mock_embed_oembed.return_value = {
            "type": "embed",
            "html": "<blockquote></blockquote>",
            "thumbnail_url": "http://pbs.twimg.com/thumb.jpg",
        }
        mock_thumb_oembed.return_value = mock_embed_oembed.return_value
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Tweet",
            content_url="https://x.com/user/status/123",
        )
        resp = self.client.get(
            reverse("post_detail", args=[self.community.slug, post.pk, post.slug])
        )
        self.assertContains(
            resp,
            'data-src="https://platform.twitter.com/embed/Tweet.html?id=123"',
        )
        self.assertContains(resp, 'href="https://x.com/user/status/123"')
        self.assertContains(resp, 'src="https://pbs.twimg.com/thumb.jpg"')

    @override_settings(ENABLE_TWITTER_EMBEDS=True)
    @patch("core.utils.thumbnails.fetch_oembed")
    @patch("core.utils.thumbnails.fetch_og_image")
    @patch("core.utils.embeds.fetch_oembed")
    def test_twitter_embed_uses_og_image_when_no_thumbnail(
        self, mock_embed_oembed, mock_fetch_og_image, mock_thumb_oembed
    ):
        mock_embed_oembed.return_value = {
            "type": "embed",
            "html": "<blockquote></blockquote>",
            "thumbnail_url": None,
        }
        mock_thumb_oembed.return_value = mock_embed_oembed.return_value
        mock_fetch_og_image.return_value = "https://pbs.twimg.com/og.jpg"
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Tweet OG",
            content_url="https://x.com/user/status/123",
        )
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, '<img src="https://pbs.twimg.com/og.jpg"')
        resp = self.client.get(
            reverse("post_detail", args=[self.community.slug, post.pk, post.slug])
        )
        self.assertContains(resp, '<img src="https://pbs.twimg.com/og.jpg"')

    @override_settings(ENABLE_TWITTER_EMBEDS=True, ENABLE_RUMBLE_EMBEDS=True)
    @patch("core.utils.thumbnails.fetch_oembed")
    @patch("core.utils.embeds.fetch_oembed")
    def test_link_thumbnail_host_matches_csp_domains(self, mock_embed_oembed, mock_thumb_oembed):
        cases = [
            (
                "https://pbs.twimg.com/thumb.jpg",
                "https://x.com/user/status/123",
            ),
            (
                "https://c.rumblecdn.com/og.jpg",
                "https://rumble.com/vxyz-test.html",
            ),
        ]
        for i, (thumb_url, content_url) in enumerate(cases, start=1):
            mock_embed_oembed.return_value = {
                "type": "embed",
                "html": "<blockquote></blockquote>",
                "thumbnail_url": thumb_url,
            }
            mock_thumb_oembed.return_value = mock_embed_oembed.return_value
            post = Post.objects.create(
                community=self.community,
                author=self.user,
                post_type="link",
                title=f"Link {i}",
                content_url=content_url,
            )
            resp = self.client.get(
                reverse("post_detail", args=[self.community.slug, post.pk, post.slug])
            )
            self.assertContains(resp, f'src="{thumb_url}"')
            parsed = urlparse(thumb_url)
            host = f"{parsed.scheme}://{parsed.netloc}"
            providers = conf_settings.EMBED_PROVIDERS
            allowed = []
            for p in providers.values():
                allowed.extend(p["img_hosts"])
            self.assertTrue(
                any(
                    host == pattern
                    or (
                        pattern.startswith("https://*.")
                        and host.endswith(pattern[len("https://*."):])
                    )
                    for pattern in allowed
                ),
                f"{host} not allowed by CSP",
            )

    def test_image_slideshow_renders(self):
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Images",
        )
        for i in range(3):
            PostImageLink.objects.create(post=post, url=f"http://example.com/{i}.jpg")
        resp = self.client.get(
            reverse("post_detail", args=[self.community.slug, post.pk, post.slug])
        )
        self.assertContains(resp, 'class="post-gallery"')
        self.assertContains(resp, 'src="https://example.com/0.jpg"')

    @override_settings(ENABLE_RUMBLE_EMBEDS=True)
    @patch("core.utils.thumbnails.fetch_oembed")
    @patch("core.utils.thumbnails.fetch_og_image")
    @patch("core.utils.embeds.fetch_oembed")
    def test_rumble_embed_uses_og_image_on_feed_and_detail(
        self, mock_embed_oembed, mock_fetch_og_image, mock_thumb_oembed
    ):
        mock_embed_oembed.return_value = {
            "type": "embed",
            "html": '<iframe src="https://rumble.com/embed/vxyz/"></iframe>',
            "thumbnail_url": None,
        }
        mock_thumb_oembed.return_value = mock_embed_oembed.return_value
        mock_fetch_og_image.return_value = "https://c.rumblecdn.com/og.jpg"
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Rumble OG",
            content_url="https://rumble.com/vxyz-test.html",
        )
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, '<img src="https://c.rumblecdn.com/og.jpg"')
        resp = self.client.get(
            reverse("post_detail", args=[self.community.slug, post.pk, post.slug])
        )
        self.assertContains(resp, '<img src="https://c.rumblecdn.com/og.jpg"')

    @override_settings(ENABLE_RUMBLE_EMBEDS=True)
    @patch("core.utils.thumbnails.fetch_oembed")
    @patch("core.utils.thumbnails.fetch_og_image")
    @patch("core.utils.embeds.fetch_oembed")
    def test_missing_thumbnail_shows_on_feed_and_detail(
        self, mock_embed_oembed, mock_fetch_og_image, mock_thumb_oembed
    ):
        mock_embed_oembed.return_value = {
            "type": "embed",
            "html": '<iframe src="https://rumble.com/embed/vxyz/"></iframe>',
            "thumbnail_url": None,
        }
        mock_thumb_oembed.return_value = mock_embed_oembed.return_value
        mock_fetch_og_image.return_value = None
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Rumble no thumb",
            content_url="https://rumble.com/vxyz-test.html",
        )
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, 'src="data:image/svg+xml;utf8,')
        resp = self.client.get(
            reverse("post_detail", args=[self.community.slug, post.pk, post.slug])
        )
        self.assertContains(resp, 'src="data:image/svg+xml;utf8,')
