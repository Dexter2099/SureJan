from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Community, Post, PostImageLink


class PostDetailMediaTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("author", password="pw")
        self.community = Community.objects.create(
            slug="test", name="Test", title="Test", created_by=self.user
        )

    @patch("core.utils.embeds.fetch_oembed")
    def test_youtube_embed_has_placeholder(self, mock_oembed):
        mock_oembed.return_value = {
            "type": "embed",
            "html": '<iframe src="https://www.youtube.com/embed/abc"></iframe>',
            "thumbnail_url": "http://img.youtube.com/vi/abc/hqdefault.jpg",
        }
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

    @patch("core.utils.embeds.fetch_oembed")
    def test_rumble_embed_has_placeholder(self, mock_oembed):
        mock_oembed.return_value = {
            "type": "embed",
            "html": '<iframe src="https://rumble.com/embed/vxyz/?pub=4"></iframe>',
            "thumbnail_url": "http://thumb.jpg",
        }
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

    @patch("core.utils.embeds.fetch_oembed")
    def test_rumble_embed_handles_single_quotes_in_iframe(self, mock_oembed):
        mock_oembed.return_value = {
            "type": "embed",
            "html": "<iframe src='https://rumble.com/embed/vxyz/?pub=4'></iframe>",
            "thumbnail_url": None,
        }
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

    @patch("core.utils.embeds.fetch_oembed")
    def test_rumble_embed_falls_back_when_no_iframe_html(self, mock_oembed):
        # oEmbed returns no iframe; builder derives /embed/<id>/ from page URL /vxyz-...
        mock_oembed.return_value = {
            "type": "embed",
            "html": "<div>no iframe here</div>",
            "thumbnail_url": None,
        }
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
