from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from core.models import Community, Post, PostImageLink


class PostImageLinkTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user("author", password="pw")
        self.community = Community.objects.create(
            slug="c", name="Comm", title="Comm", created_by=self.author
        )
        self.post = Post.objects.create(
            community=self.community,
            author=self.author,
            post_type="text",
            title="Hello",
        )

    def test_limit_of_five_links(self):
        for i in range(5):
            PostImageLink.objects.create(
                post=self.post, url=f"http://example.com/{i}.jpg"
            )
        with self.assertRaises(ValidationError):
            PostImageLink.objects.create(
                post=self.post, url="http://example.com/6.jpg"
            )

    def test_http_url_upgraded_to_https(self):
        link = PostImageLink.objects.create(
            post=self.post, url="http://example.com/img.jpg"
        )
        link.refresh_from_db()
        self.assertEqual(link.url, "https://example.com/img.jpg")
