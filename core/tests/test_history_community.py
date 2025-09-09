from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from communities.models import Community
from core.views import SORT_TABS


class HistoryCommunityRoutingTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("alice", password="pwd")
        Community.objects.create(
            slug="history", name="History", title="History", created_by=self.user
        )
        self.url = reverse("community", args=["history"])

    def test_history_feed_page_loads(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context["posts"]), [])
        self.assertEqual(resp.context["sort_tabs"], SORT_TABS)

    def test_history_sorting_and_time_filters(self):
        for sort in ["hot", "new", "top"]:
            resp = self.client.get(self.url, {"sort": sort})
            self.assertEqual(resp.status_code, 200)
        for t in ["24h", "7d", "all"]:
            resp = self.client.get(self.url, {"sort": "top", "t": t})
            self.assertEqual(resp.status_code, 200)
