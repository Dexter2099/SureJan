from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from communities.models import Community
from core.models import Post
from comments.models import Comment


class ModActionTests(TestCase):
    def setUp(self):
        cache.clear()
        U = get_user_model()
        self.user = U.objects.create_user("alice", password="pwd")
        self.staff = U.objects.create_user("mod", password="pwd", is_staff=True)
        self.community = Community.objects.create(slug="t", name="Test", title="Test", created_by=self.user)

    def test_moderator_remove_shows_message(self):
        post = Post.objects.create(community=self.community, author=self.user, post_type="text", title="Hello")
        self.client.login(username="mod", password="pwd")
        resp = self.client.post(reverse("post_remove", args=[post.pk]), HTTP_HX_REQUEST="true")
        self.assertIn(b"Removed by moderators.", resp.content)

    def test_author_soft_delete_message(self):
        post = Post.objects.create(community=self.community, author=self.user, post_type="text", title="Hi")
        Comment.objects.create(post=post, author=self.user, body="c", path="0001")
        post.comment_count = 1
        post.save(update_fields=["comment_count"])
        self.client.login(username="alice", password="pwd")
        resp = self.client.post(reverse("post_delete_owner", args=[post.pk]), HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"")

    def test_delete_window_hint(self):
        post = Post.objects.create(community=self.community, author=self.user, post_type="text", title="hint")
        self.client.login(username="alice", password="pwd")
        resp = self.client.get(reverse("post_detail", args=[self.community.slug, post.pk, post.slug]))
        self.assertEqual(resp.status_code, 200)

    def test_domain_throttle_affects_ranking(self):
        p1 = Post.objects.create(community=self.community, author=self.user, post_type="text", title="p1", score=5, content_url="https://a.com")
        p2 = Post.objects.create(community=self.community, author=self.user, post_type="text", title="p2", score=5, content_url="https://b.com")
        Post.objects.filter(pk=p1.pk).update(hot_rank=10)
        Post.objects.filter(pk=p2.pk).update(hot_rank=10)
        self.client.login(username="mod", password="pwd")
        self.client.post(reverse("post_domain_throttle", args=[p1.pk]), {"state": "1"})
        resp = self.client.get(reverse("home"))
        posts = resp.context["posts"]
        self.assertEqual(posts[0].pk, p2.pk)
