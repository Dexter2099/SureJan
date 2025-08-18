from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Community, Post
from .pagination import PAGE_SIZE, build_cursor


class PaginationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(name="t", title="Test")
        for i in range(40):
            Post.objects.create(
                community=self.community,
                author=self.user,
                post_type="text",
                title=f"Post {i}",
            )

    def test_first_page_has_cursor(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(len(resp.context["posts"]), PAGE_SIZE)
        self.assertIsNotNone(resp.context["next_before"])

    def test_load_more_htmx(self):
        resp1 = self.client.get(reverse("home"))
        cursor = resp1.context["next_before"]
        resp2 = self.client.get(
            reverse("home") + f"?before={cursor}", HTTP_HX_REQUEST="true"
        )
        self.assertNotIn("<html", resp2.content.decode())
        # Should have PAGE_SIZE posts again and not include the first page title
        self.assertEqual(resp2.content.decode().count("Post"), PAGE_SIZE)
        self.assertNotIn("Post 39", resp2.content.decode())
        self.assertNotIn("Post 25", resp2.content.decode())

    def test_last_page_no_cursor(self):
        last_post = Post.objects.order_by("created_at", "id").first()
        cursor = build_cursor(last_post)
        resp = self.client.get(reverse("home") + f"?before={cursor}")
        self.assertIsNone(resp.context.get("next_before"))
