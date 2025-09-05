from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from core.models import Comment, Community, Post


class CommentDeleteTests(TestCase):
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
        self.post.comment_count = 1
        self.post.save(update_fields=["comment_count"])
        self.url = reverse("comment_delete", args=[self.comment.pk])

    def test_author_soft_delete_htmx(self):
        self.client.login(username="alice", password="pwd")
        resp = self.client.post(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"comment deleted", resp.content)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)
        self.assertEqual(self.comment.body, "")
        self.post.refresh_from_db()
        self.assertEqual(self.post.comment_count, 1)

    def test_non_author_delete_returns_403(self):
        self.client.login(username="bob", password="pwd")
        resp = self.client.post(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 403)
        self.comment.refresh_from_db()
        self.assertFalse(self.comment.is_deleted)
