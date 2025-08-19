import datetime
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Community, Post, apply_vote


class HotRankTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )

    def test_newer_rank_higher(self):
        old = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="old",
            score=10,
        )
        Post.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - datetime.timedelta(hours=10)
        )
        old.refresh_from_db()
        old.recompute_hot()
        new = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="new",
            score=10,
        )
        new.recompute_hot()
        self.assertGreater(new.hot_rank, old.hot_rank)

    def test_vote_updates_hot(self):
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="v",
        )
        old_hot = post.hot_rank
        apply_vote(self.user, "post", post.pk, 1)
        post.refresh_from_db()
        self.assertNotEqual(post.hot_rank, old_hot)

    def test_sort_hot(self):
        p1 = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="a",
            score=10,
        )
        p1.recompute_hot()
        p2 = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="b",
            score=2,
        )
        p2.recompute_hot()
        resp = self.client.get(reverse("home") + "?t=hot")
        self.assertEqual(resp.context["posts"][0].pk, p1.pk)
