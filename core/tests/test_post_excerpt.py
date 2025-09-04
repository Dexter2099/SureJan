from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Community, Post


class PostExcerptTests(TestCase):
    def setUp(self):
        U = get_user_model()
        self.user = U.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )

    def test_excerpt_strips_html(self):
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Hello",
            body="<p>Hello <strong>world</strong></p>",
        )
        self.assertEqual(post.excerpt, "Hello world")

    def test_excerpt_truncates_long_body(self):
        long_body = "<p>" + "a" * 210 + "</p>"
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Hello",
            body=long_body,
        )
        self.assertTrue(post.excerpt.endswith("…"))
        self.assertLessEqual(len(post.excerpt), 180)

    def test_excerpt_falls_back_to_domain(self):
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Link",
            content_url="https://example.com/article",
        )
        self.assertEqual(post.excerpt, "example.com")

    def test_excerpt_empty_without_body_or_domain(self):
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="image",
            title="Image",
        )
        self.assertEqual(post.excerpt, "")
