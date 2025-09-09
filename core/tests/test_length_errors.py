from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import DataError
from django.test import TestCase
from django.urls import reverse

from communities.models import Community
from core.models import Post


class LengthErrorHandlingTests(TestCase):
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

    def test_post_submit_data_error(self):
        url = reverse("post_submit")
        data = {
            "community": self.community.pk,
            "post_type": "text",
            "title": "Hi",
            "body": "Body",
        }
        with patch("core.views.Post.save", side_effect=DataError("too long")):
            resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 400)
        self.assertIn(
            "One or more fields exceed the allowed length.",
            resp.context["form"].non_field_errors(),
        )

    def test_comment_reply_data_error(self):
        url = reverse("comment_reply", args=[self.post.pk])
        with patch(
            "comments.views.Comment.objects.create", side_effect=DataError("too long")
        ):
            resp = self.client.post(
                url, {"body": "Hi"}, HTTP_HX_REQUEST="true"
            )
        self.assertEqual(resp.status_code, 400)
        self.assertIn(
            "One or more fields exceed the allowed length.",
            resp.context["form"].non_field_errors(),
        )

    def test_comment_create_data_error(self):
        url = reverse("comment_create")
        data = {"post": self.post.pk, "body": "Hi"}
        with patch(
            "comments.views.Comment.objects.create", side_effect=DataError("too long")
        ):
            resp = self.client.post(url, data, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 400)
        self.assertIn(
            "One or more fields exceed the allowed length.",
            resp.context["form"].non_field_errors(),
        )

