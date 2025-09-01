from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Community, Post


class FeedYearFilterTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=user
        )
        now = timezone.now()
        self.p1 = Post.objects.create(
            community=self.community,
            author=user,
            post_type="text",
            title="p1",
            score=10,
        )
        self.p2 = Post.objects.create(
            community=self.community,
            author=user,
            post_type="text",
            title="p2",
            score=5,
        )
        self.old = Post.objects.create(
            community=self.community,
            author=user,
            post_type="text",
            title="old",
            score=100,
        )
        Post.objects.filter(pk=self.p1.pk).update(
            created_at=now - timedelta(days=10), hot_rank=10
        )
        Post.objects.filter(pk=self.p2.pk).update(
            created_at=now - timedelta(days=5), hot_rank=5
        )
        Post.objects.filter(pk=self.old.pk).update(
            created_at=now - timedelta(days=400), hot_rank=50
        )
        self.p1.refresh_from_db()
        self.p2.refresh_from_db()
        self.old.refresh_from_db()

    def _ids(self, tab):
        resp = self.client.get(
            reverse("feed_list"),
            {"tab": tab, "range": "year"},
            HTTP_HX_REQUEST="true",
        )
        return [p.pk for p in resp.context["posts"]]

    def test_hot_sort_year(self):
        ids = self._ids("hot")
        self.assertEqual(ids[0], self.p1.pk)
        self.assertNotIn(self.old.pk, ids)

    def test_new_sort_year(self):
        ids = self._ids("new")
        self.assertEqual(ids[:2], [self.p2.pk, self.p1.pk])
        self.assertNotIn(self.old.pk, ids)

    def test_top_sort_year(self):
        ids = self._ids("top")
        self.assertEqual(ids[0], self.p1.pk)
        self.assertNotIn(self.old.pk, ids)
