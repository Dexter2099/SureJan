from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from ..models import Community, Post


class FeedCardEmbedTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("alice", password="pw")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.factory = RequestFactory()

    @patch("core.views.build_embed_html")
    def test_feed_card_renders_embed_html(self, mock_build):
        mock_build.return_value = "<div class='post-embed'>stub</div>"
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Embed",
            content_url="https://example.com/video",
        )
        from .. import views

        request = self.factory.get("/feed", HTTP_HX_REQUEST="true")
        response = views.feed_list(request)
        html = response.content.decode()
        mock_build.assert_called_once_with(post.content_url)
        self.assertIn("post-embed", html)
