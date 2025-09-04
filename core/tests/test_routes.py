from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Community, Post


class RouteTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("tester", password="pwd")
        self.community = Community.objects.create(
            slug="test", name="Test", title="Test", created_by=self.user
        )
        self.post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Hello",
        )

    def test_home(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)

    def test_community(self):
        resp = self.client.get(reverse("community", args=[self.community.slug]))
        self.assertEqual(resp.status_code, 200)

    def test_c_prefix_redirects(self):
        resp = self.client.get(f"/c/{self.community.slug}/")
        self.assertRedirects(
            resp,
            reverse("community", args=[self.community.slug]),
            status_code=301,
        )

    def test_post_detail_id(self):
        resp = self.client.get(reverse("post_detail_id", args=[self.post.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_post_submit(self):
        self.client.login(username="tester", password="pwd")
        resp = self.client.get(reverse("post_submit"))
        self.assertEqual(resp.status_code, 200)

    def test_mod_astro(self):
        resp = self.client.get(reverse("mod_astro"))
        self.assertEqual(resp.status_code, 200)

    def test_methods(self):
        resp = self.client.get(reverse("transparency_methods"))
        self.assertEqual(resp.status_code, 200)

    def test_vote_post_htmx_returns_span(self):
        self.client.login(username="tester", password="pwd")
        url = reverse("vote_post", args=[self.post.pk])
        resp = self.client.post(f"{url}?v=1", HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertHTMLEqual(
            resp.content.decode(),
            f'<span id="post-score-{self.post.pk}" class="score">1</span>',
        )

    def test_vote_post_non_htmx_redirects(self):
        self.client.login(username="tester", password="pwd")
        url = reverse("vote_post", args=[self.post.pk])
        resp = self.client.post(f"{url}?v=1")
        self.assertRedirects(resp, self.post.get_absolute_url())
