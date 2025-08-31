from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Community, Post


class AuthFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.creator = User.objects.create_user("creator", password="pwd")
        self.community = Community.objects.create(
            slug="news", name="News", title="News", created_by=self.creator
        )

    def test_signup_login_flow(self):
        self.client.get(reverse("signup"))
        a, b = self.client.session["signup_captcha_q"]
        resp = self.client.post(
            reverse("signup"),
            {"username": "alice", "password": "secret", "captcha": a + b},
            follow=True,
        )
        self.assertContains(resp, "alice")

    def test_submit_text_post_requires_login(self):
        resp = self.client.post(
            reverse("submit_post", args=[self.community.slug]),
            {"title": "Hi", "body": "Body"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp["Location"])

    def test_submit_text_post_success(self):
        self.client.get(reverse("signup"))
        a, b = self.client.session["signup_captcha_q"]
        self.client.post(
            reverse("signup"),
            {"username": "bob", "password": "secret", "captcha": a + b},
        )
        resp = self.client.post(
            reverse("submit_post", args=[self.community.slug]),
            {"title": "Hello", "body": "World"},
        )
        self.assertRedirects(resp, reverse("community", args=[self.community.slug]))
        self.assertTrue(
            Post.objects.filter(
                community=self.community, title="Hello", author__username="bob"
            ).exists()
        )

    def test_vote_requires_login(self):
        User = get_user_model()
        author = User.objects.create_user("author", password="pwd")
        post = Post.objects.create(
            community=self.community, author=author, post_type="text", title="a"
        )
        resp = self.client.post(reverse("vote_post", args=[post.pk]) + "?v=1")
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp["Location"])
