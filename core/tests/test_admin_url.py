from django.test import TestCase, override_settings
from django.urls import reverse


class AdminURLTests(TestCase):
    def test_old_admin_url_returns_404(self):
        resp = self.client.get("/admin/", secure=True)
        self.assertEqual(resp.status_code, 404)

    def test_new_admin_url_redirects(self):
        url = reverse("admin:index")
        self.assertEqual(url, "/secret-admin/")
        resp = self.client.get(url, secure=True)
        self.assertEqual(resp.status_code, 302)

    @override_settings(ADMIN_IP_ALLOWLIST={"1.1.1.1"})
    def test_admin_blocked_for_non_allowlisted_ip(self):
        resp = self.client.get("/secret-admin/", REMOTE_ADDR="2.2.2.2", secure=True)
        self.assertEqual(resp.status_code, 403)

    @override_settings(ADMIN_IP_ALLOWLIST={"1.1.1.1"})
    def test_admin_allowed_for_allowlisted_ip(self):
        resp = self.client.get("/secret-admin/", REMOTE_ADDR="1.1.1.1", secure=True)
        self.assertEqual(resp.status_code, 302)

    @override_settings(ADMIN_IP_ALLOWLIST={"1.1.1.1"})
    def test_admin_uses_cf_connecting_ip(self):
        resp = self.client.get(
            "/secret-admin/",
            REMOTE_ADDR="2.2.2.2",
            HTTP_X_FORWARDED_FOR="3.3.3.3",
            HTTP_CF_CONNECTING_IP="1.1.1.1",
            secure=True,
        )
        self.assertEqual(resp.status_code, 302)

    @override_settings(ADMIN_IP_ALLOWLIST={"1.1.1.1"})
    def test_admin_blocks_when_cf_connecting_ip_not_allowlisted(self):
        resp = self.client.get(
            "/secret-admin/",
            REMOTE_ADDR="1.1.1.1",
            HTTP_CF_CONNECTING_IP="2.2.2.2",
            secure=True,
        )
        self.assertEqual(resp.status_code, 403)
