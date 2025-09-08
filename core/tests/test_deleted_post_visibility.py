from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Community, Post


class DeletedPostVisibilityTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.live = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Live",
            score=5,
        )
        self.deleted = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Gone",
            score=1,
            is_deleted=True,
        )

    def test_home_excludes_deleted(self):
        resp = self.client.get(reverse("home"))
        posts = resp.context["posts"]
        self.assertEqual([p.pk for p in posts], [self.live.pk])

    def test_feed_list_excludes_deleted(self):
        for tab in ["hot", "new", "top"]:
            resp = self.client.get(
                reverse("feed_list"), {"tab": tab}, HTTP_HX_REQUEST="true"
            )
            posts = resp.context["posts"]
            self.assertEqual([p.pk for p in posts], [self.live.pk])

    def test_community_excludes_deleted(self):
        resp = self.client.get(reverse("community", args=[self.community.slug]))
        posts = resp.context["posts"]
        self.assertEqual([p.pk for p in posts], [self.live.pk])
