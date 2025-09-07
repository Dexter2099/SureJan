from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import TestCase
from unittest.mock import patch

from core.utils import thumbnails
from .models import Community, Post, RateLimitCounter


def make_image(name="test.jpg"):
    img = Image.new("RGB", (10, 10), "white")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/jpeg")


class PostSubmitTests(TestCase):
    def setUp(self):
        cache.clear()
        RateLimitCounter.objects.all().delete()
        user_model = get_user_model()
        self.user = user_model.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.client.login(username="alice", password="pwd")

    def test_text_post(self):
        resp = self.client.post(
            reverse("post_submit"),
            {
                "community": self.community.id,
                "post_type": "text",
                "title": "Hello",
                "body": "World",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Post.objects.filter(title="Hello", post_type="text").exists())
        feed = self.client.get(reverse("home"))
        self.assertContains(feed, "Hello")

    def test_youtube_link_post(self):
        link = "https://www.youtube-nocookie.com/watch?v=dQw4w9WgXcQ"
        with patch("core.utils.thumbnails.resolve_thumbnail", return_value=("data:image/svg+xml;base64,ph", "alt")):
            resp = self.client.post(
                reverse("post_submit"),
                {
                    "community": self.community.id,
                    "post_type": "link",
                    "title": "YT",
                    "content_url": link,
                },
                follow=True,
            )
        self.assertEqual(resp.status_code, 200)
        post = Post.objects.get(title="YT")
        self.assertEqual(post.content_url, link)
        feed = self.client.get(reverse("home"))
        self.assertContains(feed, "YT")

    def test_link_post_remote_thumb_saved(self):
        link = "https://example.com/page"
        def fake_persist(post, url, label):
            post.image = make_image("thumb.jpg")
            post.save(update_fields=["image"])
        with patch(
            "core.utils.thumbnails.resolve_thumbnail",
            return_value=("https://cdn.example.com/thumb.jpg", "alt"),
        ), patch("core.utils.thumbnails.persist_thumbnail", side_effect=fake_persist):
            resp = self.client.post(
                reverse("post_submit"),
                {
                    "community": self.community.id,
                    "post_type": "link",
                    "title": "NoThumb",
                    "content_url": link,
                },
                follow=True,
            )
        self.assertEqual(resp.status_code, 200)
        post = Post.objects.get(title="NoThumb")
        self.assertTrue(post.image)

    def test_rumble_link_post_fetches_og_image(self):
        link = "https://rumble.com/v1abc"
        called = {}

        def fake_fetch(url):
            called["url"] = url
            thumbnails.fetch_og_image.last_status = 200
            return None

        with patch("core.utils.thumbnails.fetch_og_image", side_effect=fake_fetch) as mock_fetch, \
            patch("core.utils.thumbnails._provider_fallback", return_value=None):
            resp = self.client.post(
                reverse("post_submit"),
                {
                    "community": self.community.id,
                    "post_type": "link",
                    "title": "R", 
                    "content_url": link,
                },
                follow=True,
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(mock_fetch.call_count, 1)
        self.assertEqual(called.get("url"), link)

    def test_image_post(self):
        img = make_image()
        resp = self.client.post(
            reverse("post_submit"),
            {
                "community": self.community.id,
                "post_type": "image",
                "title": "Pic",
                "body": "Caption",
                "image": img,
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        post = Post.objects.get(title="Pic")
        self.assertIsNotNone(post.image)
        self.assertEqual(post.image_links.count(), 0)
        feed = self.client.get(reverse("home"))
        self.assertContains(feed, "Pic")

    def test_large_upload_rejected(self):
        big = SimpleUploadedFile(
            "big.jpg", b"0" * (4 * 1024 * 1024 + 1), content_type="image/jpeg"
        )
        resp = self.client.post(
            reverse("post_submit"),
            {
                "community": self.community.id,
                "post_type": "image",
                "title": "Big",
                "image": big,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Image too large (max 4MB)")
        self.assertFalse(Post.objects.filter(title="Big").exists())
