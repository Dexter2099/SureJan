"""Tests for post submission and voting endpoints."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from io import BytesIO
from PIL import Image

from ..models import Comment, Community, Post


class SubmitPostTests(TestCase):
    """Ensure users can submit text, link and image posts."""

    def setUp(self):
        cache.clear()
        user_model = get_user_model()
        self.user = user_model.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.client.login(username="alice", password="pwd")

    def test_submit_text_post(self):
        url = reverse("submit_post", args=[self.community.slug])
        resp = self.client.post(url, {"title": "Hello", "body": "Body"})
        self.assertRedirects(resp, reverse("community", args=[self.community.slug]))
        post = Post.objects.get()
        self.assertEqual(post.post_type, "text")
        self.assertEqual(post.body, "Body")
        self.assertEqual(post.url, "")

    def test_submit_link_post(self):
        url = reverse("submit_post", args=[self.community.slug])
        resp = self.client.post(
            url,
            {
                "title": "Link",
                "body": "",
                "url": "https://example.com",
            },
        )
        self.assertRedirects(resp, reverse("community", args=[self.community.slug]))
        post = Post.objects.get()
        self.assertEqual(post.post_type, "link")
        self.assertEqual(post.url, "https://example.com")
        self.assertEqual(post.body, "")

    def test_submit_image_post(self):
        url = reverse("submit_post", args=[self.community.slug])
        img = Image.new("RGB", (1, 1), color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        resp = self.client.post(
            url,
            {
                "title": "Pic",
                "body": "caption",
                "url": "",
                "image": SimpleUploadedFile("pic.png", buf.read(), content_type="image/png"),
            },
        )
        self.assertRedirects(resp, reverse("community", args=[self.community.slug]))
        post = Post.objects.get()
        self.assertEqual(post.post_type, "image")
        self.assertTrue(post.image)

    def test_requires_login(self):
        self.client.logout()
        url = reverse("submit_post", args=[self.community.slug])
        resp = self.client.post(url, {"title": "Hello", "body": "Body"})
        self.assertEqual(resp.status_code, 302)

    def test_rate_limit(self):
        url = reverse("submit_post", args=[self.community.slug])
        for i in range(3):
            self.client.post(url, {"title": f"H{i}", "body": "test"})
        resp = self.client.post(url, {"title": "H3", "body": "test"})
        self.assertEqual(resp.status_code, 429)

    def test_rate_limit_established_user(self):
        self.user.date_joined = timezone.now() - timedelta(days=2)
        self.user.save()
        url = reverse("submit_post", args=[self.community.slug])
        for i in range(10):
            resp = self.client.post(url, {"title": f"E{i}", "body": "test"})
            self.assertNotEqual(resp.status_code, 429)
        resp = self.client.post(url, {"title": "E10", "body": "test"})
        self.assertEqual(resp.status_code, 429)


class VotePostTests(TestCase):
    """Ensure voting adjusts post scores per user."""

    def setUp(self):
        cache.clear()
        user_model = get_user_model()
        self.user = user_model.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Hello",
        )
        self.client.login(username="alice", password="pwd")

    def test_upvote_post(self):
        url = reverse("vote_post", args=[self.post.pk])
        resp = self.client.post(url + "?v=1")
        self.assertEqual(resp.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 1)

    def test_downvote_post(self):
        url = reverse("vote_post", args=[self.post.pk])
        resp = self.client.post(url + "?v=-1")
        self.assertEqual(resp.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, -1)

    def test_toggle_off_post_vote(self):
        url = reverse("vote_post", args=[self.post.pk])
        self.client.post(url + "?v=1")
        self.client.post(url + "?v=1")
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 0)

    def test_switch_post_vote_direction(self):
        url = reverse("vote_post", args=[self.post.pk])
        self.client.post(url + "?v=1")
        self.client.post(url + "?v=-1")
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, -1)

    def test_switch_post_vote_back_up(self):
        url = reverse("vote_post", args=[self.post.pk])
        self.client.post(url + "?v=-1")
        self.client.post(url + "?v=1")
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 1)

    def test_invalid_vote(self):
        url = reverse("vote_post", args=[self.post.pk])
        resp = self.client.post(url + "?v=0")
        self.assertEqual(resp.status_code, 400)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 0)

    def test_requires_login(self):
        self.client.logout()
        url = reverse("vote_post", args=[self.post.pk])
        resp = self.client.post(url + "?v=1")
        self.assertEqual(resp.status_code, 302)

    def test_rate_limit(self):
        url = reverse("vote_post", args=[self.post.pk])
        for _ in range(120):
            resp = self.client.post(url + "?v=1")
            self.assertEqual(resp.status_code, 200)
        resp = self.client.post(url + "?v=1")
        self.assertEqual(resp.status_code, 429)


class VoteCommentTests(TestCase):
    """Ensure voting works for comments."""

    def setUp(self):
        cache.clear()
        user_model = get_user_model()
        self.user = user_model.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Hello",
        )
        self.comment = Comment.objects.create(
            post=self.post, author=self.user, body="Hi"
        )
        self.client.login(username="alice", password="pwd")

    def test_upvote_comment(self):
        url = reverse("vote_comment", args=[self.comment.pk])
        resp = self.client.post(url + "?v=1")
        self.assertEqual(resp.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.score, 1)

    def test_downvote_comment(self):
        url = reverse("vote_comment", args=[self.comment.pk])
        resp = self.client.post(url + "?v=-1")
        self.assertEqual(resp.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.score, -1)

    def test_toggle_off_comment_vote(self):
        url = reverse("vote_comment", args=[self.comment.pk])
        self.client.post(url + "?v=1")
        self.client.post(url + "?v=1")
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.score, 0)

    def test_switch_comment_vote_direction(self):
        url = reverse("vote_comment", args=[self.comment.pk])
        self.client.post(url + "?v=1")
        self.client.post(url + "?v=-1")
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.score, -1)

    def test_switch_comment_vote_back_up(self):
        url = reverse("vote_comment", args=[self.comment.pk])
        self.client.post(url + "?v=-1")
        self.client.post(url + "?v=1")
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.score, 1)

    def test_invalid_comment_vote(self):
        url = reverse("vote_comment", args=[self.comment.pk])
        resp = self.client.post(url + "?v=0")
        self.assertEqual(resp.status_code, 400)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.score, 0)

    def test_comment_vote_requires_login(self):
        self.client.logout()
        url = reverse("vote_comment", args=[self.comment.pk])
        resp = self.client.post(url + "?v=1")
        self.assertEqual(resp.status_code, 302)


class SortTabsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("bob", password="pwd")
        self.community = Community.objects.create(
            slug="s", name="Sample", title="Sample", created_by=self.user
        )

    def test_home_sort_tabs_active(self):
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, 'id="sort-tabs"', count=1)
        self.assertContains(
            resp, '<a href="/?sort=best" class="active">BEST</a>', html=True
        )
        resp = self.client.get(reverse("home") + "?sort=hot")
        self.assertContains(
            resp, '<a href="/?sort=hot" class="active">HOT</a>', html=True
        )
        resp = self.client.get(reverse("home") + "?sort=new")
        self.assertContains(
            resp, '<a href="/?sort=new" class="active">NEW</a>', html=True
        )

    def test_community_sort_tabs_active(self):
        url = reverse("community", args=[self.community.slug])
        resp = self.client.get(url)
        self.assertContains(resp, 'id="sort-tabs"', count=1)
        self.assertContains(
            resp,
            f'<a href="{url}?sort=best" class="active">BEST</a>',
            html=True,
        )
        resp = self.client.get(url + "?sort=hot")
        self.assertContains(
            resp,
            f'<a href="{url}?sort=hot" class="active">HOT</a>',
            html=True,
        )
        resp = self.client.get(url + "?sort=new")
        self.assertContains(
            resp,
            f'<a href="{url}?sort=new" class="active">NEW</a>',
            html=True,
        )

