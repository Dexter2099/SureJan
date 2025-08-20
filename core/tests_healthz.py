from django.test import TestCase
from django.urls import reverse


class HealthzTests(TestCase):
    def test_healthz_endpoint(self):
        resp = self.client.get(reverse("healthz"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"ok")
