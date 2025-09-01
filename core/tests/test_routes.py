from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Community, Post


class RouteTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("tester", password="pwd")
        self.community = Community.objects.create(
            slug="test", name="Test", title="Test", created_by=self.user
        )
        self.post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Hello",
        )

    def test_home(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)

    def test_community(self):
        resp = self.client.get(reverse("community", args=[self.community.slug]))
        self.assertEqual(resp.status_code, 200)

    def test_post_detail_id(self):
        resp = self.client.get(reverse("post_detail_id", args=[self.post.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_post_submit(self):
        self.client.login(username="tester", password="pwd")
        resp = self.client.get(reverse("post_submit"))
        self.assertEqual(resp.status_code, 200)

    def test_mod_astro(self):
        resp = self.client.get(reverse("mod_astro"))
        self.assertEqual(resp.status_code, 200)

    def test_methods(self):
        resp = self.client.get(reverse("transparency_methods"))
        self.assertEqual(resp.status_code, 200)
