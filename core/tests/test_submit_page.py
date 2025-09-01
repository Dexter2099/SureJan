from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache

from ..models import Community


class SubmitPageTests(TestCase):
    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.user = User.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.client.login(username="alice", password="pwd")

    def test_get_submit_page(self):
        resp = self.client.get(reverse("submit_post"))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("Submit a Post", html)
        self.assertIn('type="radio"', html)

    def test_preview_post(self):
        resp = self.client.post(
            reverse("preview_post"),
            {
                "community": self.community.pk,
                "post_type": "text",
                "title": "Hello",
                "body": "Body",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("post-preview", resp.content.decode())

    def test_text_without_body_validation(self):
        resp = self.client.post(
            reverse("submit_post"),
            {
                "community": self.community.pk,
                "post_type": "text",
                "title": "Hello",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("body", resp.context["form"].errors)

    def test_link_without_url_validation(self):
        resp = self.client.post(
            reverse("submit_post"),
            {
                "community": self.community.pk,
                "post_type": "link",
                "title": "Link",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("content_url", resp.context["form"].errors)

    def test_image_without_file_validation(self):
        resp = self.client.post(
            reverse("submit_post"),
            {
                "community": self.community.pk,
                "post_type": "image",
                "title": "Pic",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("image", resp.context["form"].errors)
