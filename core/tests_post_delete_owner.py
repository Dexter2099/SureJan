from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import Community, Post


class PostDeleteOwnerTests(TestCase):
    def setUp(self):
        cache.clear()
        U = get_user_model()
        self.user = U.objects.create_user("alice", password="pwd")
        self.other = U.objects.create_user("bob", password="pwd")
        self.staff = U.objects.create_user("mod", password="pwd", is_staff=True)
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )

    def test_author_soft_delete_htmx(self):
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Hello"
        )
        url = reverse("post_delete_owner", args=[post.pk])
        self.client.login(username="alice", password="pwd")
        resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 204)
        post.refresh_from_db()
        self.assertTrue(post.is_deleted)

    def test_author_soft_delete_redirect(self):
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Hi"
        )
        url = reverse("post_delete_owner", args=[post.pk])
        self.client.login(username="alice", password="pwd")
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        post.refresh_from_db()
        self.assertTrue(post.is_deleted)

    def test_staff_can_delete(self):
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Old"
        )
        url = reverse("post_delete_owner", args=[post.pk])
        self.client.login(username="mod", password="pwd")
        resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 204)
        post.refresh_from_db()
        self.assertTrue(post.is_deleted)

    def test_cannot_delete_others_post(self):
        post = Post.objects.create(
            community=self.community, author=self.other, post_type="text", title="Nope"
        )
        url = reverse("post_delete_owner", args=[post.pk])
        self.client.login(username="alice", password="pwd")
        resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 403)
        post.refresh_from_db()
        self.assertFalse(post.is_deleted)

    def test_requires_login(self):
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Anon"
        )
        url = reverse("post_delete_owner", args=[post.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)

    def test_banned_user_cannot_delete(self):
        self.user.profile.is_banned = True
        self.user.profile.save(update_fields=["is_banned"])
        post = Post.objects.create(
            community=self.community, author=self.user, post_type="text", title="Nope"
        )
        url = reverse("post_delete_owner", args=[post.pk])
        self.client.login(username="alice", password="pwd")
        resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 403)
        post.refresh_from_db()
        self.assertFalse(post.is_deleted)
