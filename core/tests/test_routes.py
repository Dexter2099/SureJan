from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from core.models import Community, Post
from comments.models import Comment


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
        self.comment = Comment.objects.create(
            post=self.post, author=self.user, body="Hi", path="0001"
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
        self.client.login(username="tester", password="pwd")
        resp = self.client.get(reverse("mod_astro"), follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_methods(self):
        resp = self.client.get(reverse("transparency_methods"))
        self.assertEqual(resp.status_code, 200)

    def test_vote_widget_anonymous_shows_login_prompt(self):
        rf = RequestFactory()
        request = rf.get("/")
        html_post = render_to_string(
            "core/partials/vote_widget.html", {"post": self.post}, request=request
        )
        self.assertIn("Log in to vote", html_post)
        self.assertIn(f'id="post-{self.post.pk}-score"', html_post)
        html_comment = render_to_string(
            "core/partials/vote_widget.html", {"comment": self.comment}, request=request
        )
        self.assertIn("Log in to vote", html_comment)
        self.assertIn(f'id="comment-{self.comment.pk}-score"', html_comment)

    def test_vote_post_htmx_returns_widget(self):
        self.client.login(username="tester", password="pwd")
        url = reverse("vote_post", args=[self.post.pk])
        resp = self.client.post(url, {"v": 1}, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn(f'id="post-{self.post.pk}-score"', html)
        self.assertIn("disabled", html)

    def test_vote_post_non_htmx_returns_span(self):
        self.client.login(username="tester", password="pwd")
        url = reverse("vote_post", args=[self.post.pk])
        resp = self.client.post(url, {"v": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertHTMLEqual(
            resp.content.decode(),
            f'<span id="post-{self.post.pk}-score">1</span>',
        )

    def test_vote_post_invalid_value_returns_400(self):
        self.client.login(username="tester", password="pwd")
        url = reverse("vote_post", args=[self.post.pk])
        resp = self.client.post(url, {"v": 2}, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 400)

    def test_vote_post_get_not_allowed(self):
        self.client.login(username="tester", password="pwd")
        url = reverse("vote_post", args=[self.post.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

    def test_vote_post_updates_score(self):
        self.client.login(username="tester", password="pwd")
        url = reverse("vote_post", args=[self.post.pk])
        resp = self.client.post(url, {"v": 1})
        self.assertEqual(resp.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 1)
        resp = self.client.post(url, {"v": 1})
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.content, b"")
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 1)

    def test_vote_comment_updates_score(self):
        self.client.login(username="tester", password="pwd")
        url = reverse("vote_comment", args=[self.comment.pk])
        resp = self.client.post(url, {"v": 1})
        self.assertEqual(resp.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.score, 1)
        resp = self.client.post(url, {"v": 1})
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.content, b"")
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.score, 1)

    def test_vote_comment_get_not_allowed(self):
        self.client.login(username="tester", password="pwd")
        url = reverse("vote_comment", args=[self.comment.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

    def test_vote_comment_invalid_value_returns_400(self):
        self.client.login(username="tester", password="pwd")
        url = reverse("vote_comment", args=[self.comment.pk])
        resp = self.client.post(url, {"v": 0}, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 400)

    def test_vote_comment_htmx_returns_widget(self):
        self.client.login(username="tester", password="pwd")
        url = reverse("vote_comment", args=[self.comment.pk])
        resp = self.client.post(url, {"v": 1}, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn(f'id="comment-{self.comment.pk}-score"', html)
        self.assertIn("disabled", html)

    def test_comment_row_uses_score_id_contract_without_widget(self):
        rf = RequestFactory()
        request = rf.get("/")
        html = render_to_string(
            "comments/comment_row.html",
            {"comment": self.comment, "show_vote_widget": False},
            request=request,
        )
        self.assertIn(
            f'id="comment-{self.comment.pk}-score"',
            html,
        )

    def test_vote_comment_non_htmx_returns_span(self):
        self.client.login(username="tester", password="pwd")
        url = reverse("vote_comment", args=[self.comment.pk])
        resp = self.client.post(url, {"v": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertHTMLEqual(
            resp.content.decode(),
            f'<span id="comment-{self.comment.pk}-score">1</span>',
        )

    def test_vote_comment_htmx_with_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.login(username="tester", password="pwd")
        client.get(reverse("home"))
        token = client.cookies["csrftoken"].value
        url = reverse("vote_comment", args=[self.comment.pk])
        resp = client.post(
            url,
            {"v": 1},
            HTTP_HX_REQUEST="true",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn(f'id="comment-{self.comment.pk}-score"', html)
        self.assertIn("disabled", html)
