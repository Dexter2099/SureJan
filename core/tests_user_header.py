from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class UserHeaderTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("alice", password="pwd")

    def test_header_shows_username_and_points(self):
        self.client.login(username="alice", password="pwd")
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, "alice")
        self.assertContains(resp, "Points: 0")

