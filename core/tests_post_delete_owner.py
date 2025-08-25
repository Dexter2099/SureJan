from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Comment, Community, Post


class PostDeleteOwnerTests(TestCase):
    def setUp(self):
        cache.clear()
        U = get_user_model()
        self.user = U.objects.create_user("alice", password="pwd")
        self.other = U.objects.create_user("bob", password="pwd")
        self.staff = U.objects.create_user("mod", password="pwd", is_staff=True)
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )

    def test_author_delete_without_comments_htmx(self):
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Hello"
        )
        url = reverse("post_delete_owner", args=[post.pk])
        self.client.login(username="alice", password="pwd")
        resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"")
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_author_soft_delete_with_comments_htmx(self):
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Hi"
        )
        Comment.objects.create(post=post, author=self.user, body="c", path="0001")
        post.comment_count = 1
        post.save(update_fields=["comment_count"])
        url = reverse("post_delete_owner", args=[post.pk])
        self.client.login(username="alice", password="pwd")
        resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.title, "[deleted]")
        self.assertIn(b"[deleted]", resp.content)
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

    def test_author_cannot_delete_after_window(self):
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Late"
        )
        post.created_at = timezone.now() - timedelta(minutes=16)
        post.save(update_fields=["created_at"])
        url = reverse("post_delete_owner", args=[post.pk])
        self.client.login(username="alice", password="pwd")
        resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

    def test_staff_can_delete_anytime(self):
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Old"
        )
        post.created_at = timezone.now() - timedelta(hours=1)
        post.save(update_fields=["created_at"])
        url = reverse("post_delete_owner", args=[post.pk])
        self.client.login(username="mod", password="pwd")
        resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_banned_user_cannot_delete(self):
        self.user.profile.is_banned = True
        self.user.profile.save(update_fields=["is_banned"])
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Nope"
        )
        url = reverse("post_delete_owner", args=[post.pk])
        self.client.login(username="alice", password="pwd")
        resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

    def test_rate_limit(self):
        self.client.login(username="alice", password="pwd")
        posts = [
            Post.objects.create(
                community=self.community, author=self.user, post_type="text", title=f"p{i}"
            )
            for i in range(11)
        ]
        for p in posts[:10]:
            url = reverse("post_delete_owner", args=[p.pk])
            self.client.post(url, HTTP_HX_REQUEST="true")
        resp = self.client.post(
            reverse("post_delete_owner", args=[posts[10].pk]), HTTP_HX_REQUEST="true"
        )
        self.assertEqual(resp.status_code, 429)
