"""Tests for post submission and voting endpoints."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Community, Post


class SubmitPostTests(TestCase):
    """Ensure users can submit text and link posts."""

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(name="t", title="Test")
        self.client.login(username="alice", password="pwd")

    def test_submit_text_post(self):
        url = reverse("submit_post", args=[self.community.name])
        resp = self.client.post(
            url,
            {
                "post_type": "text",
                "title": "Hello",
                "body": "Body",
                "url": "",
            },
        )
        self.assertRedirects(resp, reverse("community", args=[self.community.name]))
        post = Post.objects.get()
        self.assertEqual(post.post_type, "text")
        self.assertEqual(post.body, "Body")
        self.assertEqual(post.url, "")

    def test_submit_link_post(self):
        url = reverse("submit_post", args=[self.community.name])
        resp = self.client.post(
            url,
            {
                "post_type": "link",
                "title": "Link",
                "body": "",
                "url": "https://example.com",
            },
        )
        self.assertRedirects(resp, reverse("community", args=[self.community.name]))
        post = Post.objects.get()
        self.assertEqual(post.post_type, "link")
        self.assertEqual(post.url, "https://example.com")
        self.assertEqual(post.body, "")


class VoteTests(TestCase):
    """Ensure voting adjusts post scores."""

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(name="t", title="Test")
        self.post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Hello",
        )

    def test_upvote_post(self):
        url = reverse("vote_post", args=[self.post.pk])
        resp = self.client.post(url, {"v": "1"})
        self.assertEqual(resp.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 1)

    def test_downvote_post(self):
        url = reverse("vote_post", args=[self.post.pk])
        resp = self.client.post(url, {"v": "-1"})
        self.assertEqual(resp.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, -1)

    def test_invalid_vote(self):
        url = reverse("vote_post", args=[self.post.pk])
        resp = self.client.post(url, {"v": "0"})
        self.assertEqual(resp.status_code, 400)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 0)

