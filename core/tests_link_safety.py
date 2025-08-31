from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from .models import Community, Post


class LinkSafetyTests(TestCase):
    def setUp(self):
        cache.clear()
        user_model = get_user_model()
        self.user = user_model.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.client.login(username="alice", password="pwd")
        self.url = reverse("submit_post", args=[self.community.slug])

    @override_settings(URL_REPUTATION_API_KEY="k")
    @patch("core.utils.link_safety.requests.post")
    def test_safe_url_allowed(self, mock_post):
        mock_post.return_value.json.return_value = {}
        mock_post.return_value.status_code = 200
        resp = self.client.post(
            self.url,
            {"title": "Link", "body": "", "url": "https://example.com"},
        )
        self.assertRedirects(resp, reverse("community", args=[self.community.slug]))
        self.assertEqual(Post.objects.count(), 1)

    @override_settings(URL_REPUTATION_API_KEY="k")
    @patch("core.utils.link_safety.requests.post")
    def test_unsafe_url_rejected(self, mock_post):
        mock_post.return_value.json.return_value = {
            "matches": [{"threatType": "MALWARE"}]
        }
        mock_post.return_value.status_code = 200
        resp = self.client.post(
            self.url,
            {"title": "Bad", "body": "", "url": "http://malware.test"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp.context["form"], "url", "URL flagged as unsafe.")
        self.assertEqual(Post.objects.count(), 0)
