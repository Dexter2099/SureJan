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
        self.post.comment_count = 1
        self.post.save(update_fields=["comment_count"])
        self.url = reverse("comment_delete", args=[self.comment.pk])
        self.client.login(username="alice", password="pwd")

    def test_delete_own_comment(self):
        resp = self.client.post(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())
        self.post.refresh_from_db()
        self.assertEqual(self.post.comment_count, 0)

    def test_staff_can_delete(self):
        self.client.logout()
        self.client.login(username="mod", password="pwd")
        resp = self.client.post(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_cannot_delete_others_comment(self):
        self.client.logout()
        self.client.login(username="bob", password="pwd")
        resp = self.client.post(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_requires_login(self):
        self.client.logout()
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_delete_subtree_decrements_count(self):
        child = Comment.objects.create(
            post=self.post,
            author=self.user,
            parent=self.comment,
            body="child",
            path="0001/0001",
        )
        self.post.comment_count = 2
        self.post.save(update_fields=["comment_count"])
        resp = self.client.post(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Comment.objects.count(), 0)
        self.post.refresh_from_db()
        self.assertEqual(self.post.comment_count, 0)

