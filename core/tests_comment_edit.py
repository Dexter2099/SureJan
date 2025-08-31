from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Comment, Community, Post


class CommentEditTests(TestCase):
    def setUp(self):
        cache.clear()
        U = get_user_model()
        self.user = U.objects.create_user("alice", password="pwd")
        self.other = U.objects.create_user("bob", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Hello",
        )
        self.comment = Comment.objects.create(
            post=self.post, author=self.user, body="Hi", path="0001"
        )
        self.url = reverse("comment_edit", args=[self.comment.pk])
        self.client.login(username="alice", password="pwd")

    def test_author_can_edit_within_window(self):
        resp = self.client.get(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(self.url, {"body": "Updated"}, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.body, "Updated")
        self.assertIsNotNone(self.comment.edited_at)
        self.assertIn("edited", resp.content.decode())

    def test_cannot_edit_after_window(self):
        Comment.objects.filter(pk=self.comment.pk).update(
            created_at=timezone.now() - timedelta(minutes=16)
        )
        resp = self.client.get(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 403)

    def test_other_user_cannot_edit(self):
        self.client.logout()
        self.client.login(username="bob", password="pwd")
        resp = self.client.get(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 403)

