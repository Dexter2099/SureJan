from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Community


class CommunityCreateTests(TestCase):
    def setUp(self):
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
            {"name": "test", "title": "Test", "description": ""},
        )
        self.assertRedirects(resp, reverse("community", args=["test"]))
        self.assertTrue(Community.objects.filter(name="test").exists())

    def test_b_non_staff_forbidden(self):
        self.client.login(username="user", password="pwd")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_c_duplicate_rejected(self):
        Community.objects.create(name="dup", title="Dup")
        self.client.login(username="staff", password="pwd")
        resp = self.client.post(
            self.url,
            {"name": "dup", "title": "Another", "description": ""},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, "form", "name", "Community with this name already exists.")

    def test_d_rate_limit(self):
        self.client.login(username="staff", password="pwd")
        for i in range(5):
            self.client.post(self.url, {"name": f"c{i}", "title": "t"})
        resp = self.client.post(self.url, {"name": "c6", "title": "t"})
        self.assertEqual(resp.status_code, 429)
