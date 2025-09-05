from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Community, Post


class CommentDeleteTests(TestCase):
    def setUp(self):
        cache.clear()
        U = get_user_model()
        self.user = U.objects.create_user("alice", password="pwd")
        self.other = U.objects.create_user("bob", password="pwd")
        self.staff = U.objects.create_user("mod", password="pwd", is_staff=True)
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
        self.url = reverse("comment_delete", args=[self.comment.pk])
        self.client.login(username="alice", password="pwd")

    def test_delete_own_comment_htmx(self):
        resp = self.client.post(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'hx-swap="outerHTML"', resp.content)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)
        self.assertEqual(self.comment.body, "")

    def test_delete_own_comment_redirect(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)

    def test_staff_can_delete(self):
        self.client.logout()
        self.client.login(username="mod", password="pwd")
        resp = self.client.post(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)
        self.assertIn(b"Removed by moderators", resp.content)

    def test_cannot_delete_others_comment(self):
        self.client.logout()
        self.client.login(username="bob", password="pwd")
        resp = self.client.post(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 403)
        self.comment.refresh_from_db()
        self.assertFalse(self.comment.is_deleted)

    def test_requires_login(self):
        self.client.logout()
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)

