from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import Community, Post


class PostURLCanonicalizationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("alice", password="pw")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )

    def test_rumble_url_query_cleaned(self):
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Rumble",
            content_url="https://rumble.com/v1abcd-something.html?foo=bar",
        )
        post.refresh_from_db()
        self.assertEqual(
            post.content_url, "https://rumble.com/v1abcd-something.html"
        )
        self.assertEqual(post.link_domain, "rumble.com")
