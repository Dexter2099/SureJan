from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from django.test import TestCase
from communities.models import Community
from core.models import Post, RateLimitCounter


class PostSubmitTests(TestCase):
    def setUp(self):
        cache.clear()
        RateLimitCounter.objects.all().delete()
        user_model = get_user_model()
        self.user = user_model.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.client.login(username="alice", password="pwd")

    def test_text_post(self):
        resp = self.client.post(
            reverse("post_submit"),
            {
                "community": self.community.id,
                "post_type": "text",
                "title": "Hello",
                "body": "World",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Post.objects.filter(title="Hello", post_type="text").exists())
        feed = self.client.get(reverse("home"))
        self.assertContains(feed, "Hello")

    def test_link_post(self):
        link = "https://example.com/page"
        resp = self.client.post(
            reverse("post_submit"),
            {
                "community": self.community.id,
                "post_type": "link",
                "title": "Link",
                "content_url": link,
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        post = Post.objects.get(title="Link")
        self.assertEqual(post.content_url, link)
        feed = self.client.get(reverse("home"))
        self.assertContains(feed, "Link")

