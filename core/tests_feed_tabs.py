from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Community, Post


class FeedTabOrderTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=user
        )
        self.old = Post.objects.create(
            community=self.community,
            author=user,
            post_type="text",
            title="old",
            score=5,
        )
        self.new = Post.objects.create(
            community=self.community,
            author=user,
            post_type="text",
            title="new",
            score=3,
        )
        # Give the older post better rankings so ordering is obvious
        Post.objects.filter(pk=self.old.pk).update(
            best_rank=10, rising_rank=10, controversy=10, hot_rank=10
        )
        Post.objects.filter(pk=self.new.pk).update(
            best_rank=1, rising_rank=1, controversy=1, hot_rank=1
        )
        self.old.refresh_from_db()
        self.new.refresh_from_db()

    def _first_post(self, tab):
        resp = self.client.get(
            reverse("feed_list"), {"tab": tab, "range": "24h"}, HTTP_HX_REQUEST="true"
        )
        return resp.context["posts"][0]

    def test_hot_order(self):
        self.assertEqual(self._first_post("hot").pk, self.old.pk)

    def test_new_order(self):
        self.assertEqual(self._first_post("new").pk, self.new.pk)

    def test_rising_order(self):
        self.assertEqual(self._first_post("rising").pk, self.old.pk)

    def test_controversial_order(self):
        self.assertEqual(self._first_post("controversial").pk, self.old.pk)

    def test_top_order(self):
        self.assertEqual(self._first_post("top").pk, self.old.pk)


class CommunityFeedTabOrderTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=user
        )
        self.old = Post.objects.create(
            community=self.community,
            author=user,
            post_type="text",
            title="old",
            score=5,
        )
        self.new = Post.objects.create(
            community=self.community,
            author=user,
            post_type="text",
            title="new",
            score=3,
        )
        Post.objects.filter(pk=self.old.pk).update(
            best_rank=10, rising_rank=10, controversy=10, hot_rank=10
        )
        Post.objects.filter(pk=self.new.pk).update(
            best_rank=1, rising_rank=1, controversy=1, hot_rank=1
        )
        self.old.refresh_from_db()
        self.new.refresh_from_db()

    def _first_post(self, tab):
        url = reverse("community", args=[self.community.slug]) + f"?sort={tab}"
        resp = self.client.get(url)
        return resp.context["posts"][0]

    def test_best_order(self):
        self.assertEqual(self._first_post("best").pk, self.old.pk)

    def test_new_order(self):
        self.assertEqual(self._first_post("new").pk, self.new.pk)

    def test_rising_order(self):
        self.assertEqual(self._first_post("rising").pk, self.old.pk)

    def test_controversial_order(self):
        self.assertEqual(self._first_post("controversial").pk, self.old.pk)

    def test_top_order(self):
        self.assertEqual(self._first_post("top").pk, self.old.pk)
