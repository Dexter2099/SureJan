from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from core.models import Community


class CommunityCreateTests(TestCase):
    def setUp(self):
        cache.clear()
        user_model = get_user_model()
        self.staff = user_model.objects.create_user("staff", password="pwd", is_staff=True)
        self.user = user_model.objects.create_user("user", password="pwd")
        self.url = reverse("community_create")

    def test_a_staff_can_view_and_create(self):
        self.client.login(username="staff", password="pwd")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(
            self.url,
            {"slug": "test", "name": "Test", "title": "Test", "description": ""},
        )
        self.assertRedirects(resp, reverse("community", args=["test"]))
        self.assertTrue(Community.objects.filter(slug="test").exists())

    def test_b_non_staff_forbidden(self):
        self.client.login(username="user", password="pwd")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_c_duplicate_rejected(self):
        Community.objects.create(
            slug="dup", name="Dup", title="Dup", created_by=self.staff
        )
        self.client.login(username="staff", password="pwd")
        resp = self.client.post(
            self.url,
            {"slug": "dup", "name": "Dup", "title": "Another", "description": ""},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(
            resp.context["form"],
            "slug",
            "Community with this slug already exists.",
        )

    def test_d_rate_limit(self):
        self.client.login(username="staff", password="pwd")
        for i in range(5):
            self.client.post(
                self.url,
                {"slug": f"c{i}", "name": f"C{i}", "title": "t"},
            )
        resp = self.client.post(
            self.url, {"slug": "c6", "name": "C6", "title": "t"}
        )
        self.assertEqual(resp.status_code, 429)

