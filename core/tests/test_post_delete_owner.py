from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from core.models import Community, Post
from votes.models import Vote
from votes.services import cast_vote_post_once


class PostDeleteOwnerTests(TestCase):
    def setUp(self):
        cache.clear()
        U = get_user_model()
        self.user = U.objects.create_user("alice", password="pwd")
        self.other = U.objects.create_user("bob", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )

    def test_author_soft_delete_htmx(self):
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Hello"
        )
        cast_vote_post_once(self.other, post, 1)
        votes_before = Vote.objects.filter(target_type="post", target_id=post.pk).count()

        # Post appears in global feed
        resp = self.client.get(reverse("feed_list"), HTTP_HX_REQUEST="true")
        self.assertIn(b"Hello", resp.content)

        self.client.login(username="alice", password="pwd")
        url = reverse("post_delete_owner", args=[post.pk])
        resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"")
        self.assertEqual(resp["Content-Type"], "text/html")
        post.refresh_from_db()
        self.assertTrue(post.is_deleted)
        self.assertEqual(post.score, 1)
        votes_after = Vote.objects.filter(target_type="post", target_id=post.pk).count()
        self.assertEqual(votes_before, votes_after)

        # Post removed from feed and detail page not found
        resp = self.client.get(reverse("feed_list"), HTTP_HX_REQUEST="true")
        self.assertNotIn(b"Hello", resp.content)
        resp = self.client.get(post.get_absolute_url())
        self.assertEqual(resp.status_code, 404)

    def test_non_author_delete_returns_403(self):
        post = Post.objects.create(
            community=self.community, author=self.other, post_type="text", title="Nope"
        )
        self.client.login(username="alice", password="pwd")
        url = reverse("post_delete_owner", args=[post.pk])
        resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 403)
        post.refresh_from_db()
        self.assertFalse(post.is_deleted)

    def test_author_soft_delete_htmx_detail_redirect(self):
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Hi"
        )
        self.client.login(username="alice", password="pwd")
        url = reverse("post_delete_owner", args=[post.pk])
        resp = self.client.post(url, {"from": "detail"}, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.headers["HX-Redirect"],
            reverse("community", args=[self.community.slug]),
        )
        post.refresh_from_db()
        self.assertTrue(post.is_deleted)

    def test_author_soft_delete_redirect(self):
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Hi"
        )
        self.client.login(username="alice", password="pwd")
        url = reverse("post_delete_owner", args=[post.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        post.refresh_from_db()
        self.assertTrue(post.is_deleted)

    def test_staff_can_delete(self):
        staff = get_user_model().objects.create_user(
            "mod", password="pwd", is_staff=True
        )
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Old"
        )
        self.client.login(username="mod", password="pwd")
        url = reverse("post_delete_owner", args=[post.pk])
        resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"")
        self.assertNotIn("HX-Redirect", resp.headers)
        post.refresh_from_db()
        self.assertTrue(post.is_deleted)

    def test_requires_login(self):
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Anon"
        )
        url = reverse("post_delete_owner", args=[post.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)

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
        post.refresh_from_db()
        self.assertFalse(post.is_deleted)

    def test_soft_delete_preserves_votes_and_metrics(self):
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Keep"
        )
        cast_vote_post_once(self.other, post, 1)
        url = reverse("post_delete_owner", args=[post.pk])
        self.client.login(username="alice", password="pwd")
        with patch("core.models.Post.recompute_hot") as mock_recompute:
            resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"")
        self.assertNotIn("HX-Redirect", resp.headers)
        mock_recompute.assert_not_called()
        post.refresh_from_db()
        self.assertTrue(post.is_deleted)
        self.assertEqual(post.score, 1)
        votes = Vote.objects.filter(target_type="post", target_id=post.pk).count()
        self.assertEqual(votes, 1)
