from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Community, Post


class FeedRangeMixin:
    def setUp(self):
        user = get_user_model().objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=user
        )
        now = timezone.now()
        self.day_post = Post.objects.create(
            community=self.community,
            author=user,
            post_type="text",
            title="d",
            score=1,
        )
        self.week_post = Post.objects.create(
            community=self.community,
            author=user,
            post_type="text",
            title="w",
            score=1,
        )
        self.month_post = Post.objects.create(
            community=self.community,
            author=user,
            post_type="text",
            title="m",
            score=1,
        )
        self.year_post = Post.objects.create(
            community=self.community,
            author=user,
            post_type="text",
            title="y",
            score=1,
        )
        self.old_post = Post.objects.create(
            community=self.community,
            author=user,
            post_type="text",
            title="o",
            score=1,
        )
        Post.objects.filter(pk=self.day_post.pk).update(created_at=now - timedelta(hours=12))
        Post.objects.filter(pk=self.week_post.pk).update(created_at=now - timedelta(days=3))
        Post.objects.filter(pk=self.month_post.pk).update(created_at=now - timedelta(days=20))
        Post.objects.filter(pk=self.year_post.pk).update(created_at=now - timedelta(days=100))
        Post.objects.filter(pk=self.old_post.pk).update(created_at=now - timedelta(days=400))
        for p in [
            self.day_post,
            self.week_post,
            self.month_post,
            self.year_post,
            self.old_post,
        ]:
            p.refresh_from_db()


class FeedRangeFilterHTMXTests(FeedRangeMixin, TestCase):
    def _ids(self, t):
        params = {"tab": "top"}
        if t is not None:
            params["t"] = t
        resp = self.client.get(reverse("feed_list"), params, HTTP_HX_REQUEST="true")
        return [p.pk for p in resp.context["posts"]]

    def test_24h_filter(self):
        ids = self._ids("24h")
        self.assertEqual(ids, [self.day_post.pk])
        self.assertNotIn(self.week_post.pk, ids)

    def test_7d_filter(self):
        ids = self._ids("7d")
        self.assertSetEqual(set(ids), {self.day_post.pk, self.week_post.pk})

    def test_all_filter(self):
        ids = self._ids("all")
        self.assertSetEqual(
            set(ids),
            {
                self.day_post.pk,
                self.week_post.pk,
                self.month_post.pk,
                self.year_post.pk,
                self.old_post.pk,
            },
        )

    def test_default_all(self):
        ids = self._ids(None)
        self.assertSetEqual(
            set(ids),
            {
                self.day_post.pk,
                self.week_post.pk,
                self.month_post.pk,
                self.year_post.pk,
                self.old_post.pk,
            },
        )


class FeedRangeFilterHomeTests(FeedRangeMixin, TestCase):
    def _ids(self, t):
        params = {"tab": "top"}
        if t is not None:
            params["t"] = t
        resp = self.client.get(reverse("home"), params)
        return [p.pk for p in resp.context["page"].object_list]

    def test_24h_filter(self):
        ids = self._ids("24h")
        self.assertEqual(ids, [self.day_post.pk])
        self.assertNotIn(self.week_post.pk, ids)

    def test_7d_filter(self):
        ids = self._ids("7d")
        self.assertSetEqual(set(ids), {self.day_post.pk, self.week_post.pk})

    def test_all_filter(self):
        ids = self._ids("all")
        self.assertSetEqual(
            set(ids),
            {
                self.day_post.pk,
                self.week_post.pk,
                self.month_post.pk,
                self.year_post.pk,
                self.old_post.pk,
            },
        )

    def test_default_all(self):
        ids = self._ids(None)
        self.assertSetEqual(
            set(ids),
            {
                self.day_post.pk,
                self.week_post.pk,
                self.month_post.pk,
                self.year_post.pk,
                self.old_post.pk,
            },
        )
