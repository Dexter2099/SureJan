from django.test import TestCase
from django.urls import reverse


class CommunitiesIndexTests(TestCase):
    def test_lists_communities(self):
        resp = self.client.get(reverse("communities_index"))
        for name in ["News", "Brisbane", "Politics", "Social"]:
            self.assertContains(resp, name)

    def test_header_sort_highlight(self):
        resp = self.client.get(reverse("communities_index"), {"sort": "new"})
        self.assertContains(resp, 'href="?sort=new" aria-current="page"')
