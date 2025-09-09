from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from communities.models import Community
from core.models import Post
from core.pagination import PAGE_SIZE


class PaginationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="news", name="News", title="News", created_by=self.user
        )
        for i in range(40):
            Post.objects.create(
                community=self.community,
                author=self.user,
                post_type="text",
                title=f"Post {i}",
            )

    def test_first_page_has_next(self):
        resp = self.client.get(reverse("feed_list"), HTTP_HX_REQUEST="true")
        self.assertEqual(len(resp.context["posts"]), PAGE_SIZE)
        self.assertEqual(resp.context["next_page"], 2)

    def test_load_more_htmx(self):
        resp1 = self.client.get(reverse("feed_list"), HTTP_HX_REQUEST="true")
        next_page = resp1.context["next_page"]
        resp2 = self.client.get(
            reverse("feed_list") + f"?page={next_page}", HTTP_HX_REQUEST="true"
        )
        body = resp2.content.decode()
        self.assertNotIn("<html", body)
        # Should have PAGE_SIZE posts again and not include the first page title
        self.assertEqual(body.count("Post"), PAGE_SIZE)
        self.assertNotIn("Post 39", body)
        self.assertNotIn("Post 25", body)

    def test_last_page_no_next(self):
        resp = self.client.get(reverse("feed_list") + "?page=3", HTTP_HX_REQUEST="true")
        self.assertIsNone(resp.context.get("next_page"))

    def test_out_of_range_page_clamped(self):
        url = reverse("community", kwargs={"slug": self.community.slug}) + "?page=9999"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # 40 posts with PAGE_SIZE 15 -> last page has 10 posts
        self.assertEqual(len(resp.context["posts"]), 40 - 2 * PAGE_SIZE)
        self.assertIsNone(resp.context.get("next_page"))
