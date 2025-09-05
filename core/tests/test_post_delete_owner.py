from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from core.models import Community, Post, Vote
from core.services.votes import cast_vote_post_once


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
