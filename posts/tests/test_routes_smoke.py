from django.test import TestCase
from django.urls import reverse


class RouteSmokeTests(TestCase):
    def test_home_route_has_nav_tabs(self):
        url = reverse("home")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Check navbar tabs are present
        self.assertContains(resp, 'id="sort-tabs"')
        for tab in ("Hot", "New", "Top"):
            self.assertContains(resp, tab)

    def test_healthz_route(self):
        url = reverse("healthz")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"ok")
