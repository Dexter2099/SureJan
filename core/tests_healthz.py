from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.db.utils import OperationalError


class HealthzTests(TestCase):
    def test_healthz_endpoint(self):
        resp = self.client.get(reverse("healthz"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"ok")

    @patch("core.views.connections")
    def test_healthz_db_failure(self, mock_connections):
        mock_connections.__getitem__.return_value.cursor.side_effect = OperationalError
        resp = self.client.get(reverse("healthz"))
        self.assertEqual(resp.status_code, 500)

    @patch("core.views.cache")
    def test_healthz_cache_failure(self, mock_cache):
        mock_cache.set.side_effect = Exception
        resp = self.client.get(reverse("healthz"))
        self.assertEqual(resp.status_code, 500)
