from unittest.mock import patch
import subprocess
import textwrap

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from ..models import Community, Post
from .. import views


class FeedThumbnailTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("alice", password="pw")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.factory = RequestFactory()

    @patch("core.views.resolve_thumbnail")
    def test_feed_card_uses_thumbnail(self, mock_thumb):
        mock_thumb.return_value = ("https://cdn.example/thumb.jpg", "Preview")
        Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Embed",
            content_url="https://example.com/video",
        )
        request = self.factory.get("/feed", HTTP_HX_REQUEST="true")
        response = views.feed_list(request)
        html = response.content.decode()
        self.assertIn("https://cdn.example/thumb.jpg", html)
        self.assertIn("play-overlay", html)
        self.assertNotIn("<iframe", html)

    def test_detail_click_loads_iframe(self):
        subprocess.run(
            ["npm", "install", "jsdom@22.1.0", "--no-save"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        script = textwrap.dedent(
            """
            const {JSDOM} = require('jsdom');
            const fs = require('fs');
            const dom = new JSDOM('<div class="post-embed" data-src="https://embed.example"><a href="https://example" rel="noopener"><img src="t.jpg" alt="a"></a></div>');
            const window = dom.window; const document = window.document;
            global.window = window; global.document = document;
            const code = fs.readFileSync('static/js/embeds.js', 'utf8');
            eval(code);
            window.initEmbeds(document);
            const link = document.querySelector('a');
            link.dispatchEvent(new window.Event('click', { bubbles: true }));
            const iframe = document.querySelector('iframe');
            console.log(iframe ? iframe.outerHTML : '');
            """
        )
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
        out = result.stdout.strip()
        self.assertIn("<iframe", out)
        self.assertIn('allowfullscreen', out)
        self.assertIn('referrerpolicy="no-referrer"', out)
