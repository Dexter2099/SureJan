from django.test import TestCase
from django.urls import reverse


class AdminURLTests(TestCase):
    def test_old_admin_url_returns_404(self):
        resp = self.client.get("/admin/", secure=True)
        self.assertEqual(resp.status_code, 404)

    def test_new_admin_url_redirects(self):
        url = reverse("admin:index")
        self.assertEqual(url, "/_sj-admin-8h9ks3/")
        resp = self.client.get(url, secure=True)
        self.assertEqual(resp.status_code, 302)
