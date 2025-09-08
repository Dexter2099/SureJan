from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Community, Post


class BanUserTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            "mod", password="pwd", is_staff=True
        )
        self.user = User.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.staff
        )
        self.post = Post.objects.create(
            community=self.community,
            author=self.staff,
            post_type="text",
            title="hello",
        )

    def test_ban_and_unban_user(self):
        self.client.login(username="mod", password="pwd")
        resp = self.client.post(reverse("ban_user", args=[self.user.username]))
        self.assertRedirects(resp, reverse("user_overview", args=[self.user.username]))
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile.is_banned)

        self.client.logout()
        self.client.login(username="alice", password="pwd")
        resp = self.client.post(
            reverse("comment_reply", args=[self.post.pk]), {"body": "hi"}
        )
        self.assertEqual(resp.status_code, 403)

        self.client.logout()
        self.client.login(username="mod", password="pwd")
        self.client.post(reverse("unban_user", args=[self.user.username]))
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile.is_banned)
