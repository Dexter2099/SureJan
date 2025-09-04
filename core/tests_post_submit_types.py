from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import TestCase

from .models import Community, Post


def make_image(name="test.jpg"):
    img = Image.new("RGB", (10, 10), "white")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/jpeg")


class PostSubmitTests(TestCase):
    def setUp(self):
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

    def test_three_image_post(self):
        imgs = [make_image(f"i{i}.jpg") for i in range(3)]
        resp = self.client.post(
            reverse("post_submit"),
            {
                "community": self.community.id,
                "post_type": "images",
                "title": "Pics",
                "body": "Caption",
                "images": imgs,
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        post = Post.objects.get(title="Pics")
        self.assertIsNotNone(post.image)
        self.assertEqual(post.image_links.count(), 2)
        feed = self.client.get(reverse("home"))
        self.assertContains(feed, "Pics")

    def test_large_upload_rejected(self):
        big = SimpleUploadedFile(
            "big.jpg", b"0" * (4 * 1024 * 1024 + 1), content_type="image/jpeg"
        )
        resp = self.client.post(
            reverse("post_submit"),
            {
                "community": self.community.id,
                "post_type": "images",
                "title": "Big",
                "images": [big],
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Image too large (max 4MB)")
        self.assertFalse(Post.objects.filter(title="Big").exists())
