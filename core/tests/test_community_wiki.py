from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from communities.models import Community


class CommunityWikiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("user", password="pwd")
        self.community = Community.objects.create(
            slug="test", name="Test", title="Test", created_by=self.user
        )

    def test_a_stub_when_missing(self):
        url = reverse("community_wiki", args=[self.community.slug])
        resp = self.client.get(url)
        self.assertContains(resp, "Community wiki coming soon.")

    def test_b_render_html_when_present(self):
        self.community.wiki_html = "<p>Hello</p>"
        self.community.save()
        url = reverse("community_wiki", args=[self.community.slug])
        resp = self.client.get(url)
        self.assertContains(resp, "<p>Hello</p>", html=True)

