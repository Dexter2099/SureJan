from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from communities.models import Community
from core.models import Post
from votes.models import Vote
from comments.models import Comment
from votes.services import cast_vote_comment_once


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

    def test_author_delete_redirect(self):
        self.client.login(username="alice", password="pwd")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)

    def test_staff_can_delete(self):
        staff = get_user_model().objects.create_user(
            "mod", password="pwd", is_staff=True
        )
        self.client.login(username="mod", password="pwd")
        resp = self.client.post(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"comment deleted", resp.content)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)

    def test_requires_login(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_delete_preserves_votes_and_skips_recompute(self):
        other = get_user_model().objects.create_user("charlie", password="pwd")
        cast_vote_comment_once(other, self.comment, 1)
        votes_before = Vote.objects.filter(
            target_type="comment", target_id=self.comment.pk
        ).count()
        self.client.login(username="alice", password="pwd")
        with patch("votes.models.Vote.objects.filter") as mock_filter:
            resp = self.client.post(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        mock_filter.assert_not_called()
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)
        self.assertEqual(self.comment.score, 1)
        votes_after = Vote.objects.filter(
            target_type="comment", target_id=self.comment.pk
        ).count()
        self.assertEqual(votes_before, votes_after)
