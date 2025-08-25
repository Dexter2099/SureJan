from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Comment, Community, Post


class CommentReplyTests(TestCase):
    def setUp(self):
        cache.clear()
        user_model = get_user_model()
        self.user = user_model.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Hello",
        )
        self.url = reverse("comment_reply", args=[self.post.pk])
        self.client.login(username="alice", password="pwd")

    def test_create_root_comment(self):
        resp = self.client.post(self.url, {"body": "Hi"}, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        comment = Comment.objects.get()
        self.assertEqual(comment.path, "0001")
        self.post.refresh_from_db()
        self.assertEqual(self.post.comment_count, 1)
        self.assertIn(b"Hi", resp.content)

    def test_reply_to_comment(self):
        self.client.post(self.url, {"body": "Root"}, HTTP_HX_REQUEST="true")
        root = Comment.objects.get()
        resp = self.client.post(
            self.url,
            {"body": "Child", "parent_id": root.pk},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)
        child = Comment.objects.exclude(pk=root.pk).get()
        self.assertEqual(child.path, "0001/0001")
        self.post.refresh_from_db()
        self.assertEqual(self.post.comment_count, 2)

    def test_requires_login(self):
        self.client.logout()
        resp = self.client.post(self.url, {"body": "Hi"})
        self.assertEqual(resp.status_code, 302)

    def test_rate_limit(self):
        for i in range(3):
            self.client.post(self.url, {"body": f"c{i}"}, HTTP_HX_REQUEST="true")
        resp = self.client.post(self.url, {"body": "c3"}, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 429)

    def test_rate_limit_established_user(self):
        self.user.date_joined = timezone.now() - timedelta(days=2)
        self.user.save()
        for i in range(10):
            resp = self.client.post(
                self.url,
                {"body": f"e{i}"},
                HTTP_HX_REQUEST="true",
            )
            self.assertNotEqual(resp.status_code, 429)
        resp = self.client.post(self.url, {"body": "e10"}, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 429)
