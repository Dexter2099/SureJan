from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.urls import reverse
from io import BytesIO
from PIL import Image

from ..models import Comment, Community, Post


class CommentLinkTests(TestCase):
    def setUp(self):
        cache.clear()
        U = get_user_model()
        self.user = U.objects.create_user("alice", password="pwd")
        self.other = U.objects.create_user("bob", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Hello",
        )

    def test_post_detail_comment_links(self):
        root = Comment.objects.create(
            post=self.post, author=self.user, body="root", path="0001"
        )
        child = Comment.objects.create(
            post=self.post,
            author=self.other,
            parent=root,
            body="child",
            path="0001/0001",
        )
        self.post.comment_count = 2
        self.post.save(update_fields=["comment_count"])

        url = reverse(
            "post_detail", args=[self.community.slug, self.post.pk, self.post.slug]
        )
        self.assertEqual(
            url,
            f"/r/{self.community.slug}/comments/{self.post.pk}/{self.post.slug}",
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        for comment in (root, child):
            self.assertContains(resp, f'id="c{comment.pk}"')
            user_url = reverse("user_overview", args=[comment.author.username])
            self.assertEqual(user_url, f"/u/{comment.author.username}/")
            self.assertContains(resp, f'href="{user_url}"')


class PostLinkTests(TestCase):
    def setUp(self):
        cache.clear()
        U = get_user_model()
        self.user = U.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        buf = BytesIO()
        Image.new("RGB", (1, 1)).save(buf, format="PNG")
        img = SimpleUploadedFile("a.png", buf.getvalue(), content_type="image/png")
        self.post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="image",
            title="Hello",
            image=img,
        )
        self.factory = RequestFactory()

    def test_feed_card_uses_absolute_url(self):
        url = self.post.get_absolute_url()
        request = self.factory.get("/")
        html = render_to_string("partials/feed_card.html", {"post": self.post}, request=request)
        self.assertEqual(html.count(f'href="{url}"'), 2)
        self.assertIn(f'href="{url}#comments"', html)

    def test_post_row_uses_absolute_url(self):
        url = self.post.get_absolute_url()
        request = self.factory.get("/")
        html = render_to_string("core/partials/post_row.html", {"post": self.post}, request=request)
        self.assertEqual(html.count(f'href="{url}"'), 2)
        self.assertIn(f'href="{url}#comments"', html)

    def test_post_row_links_author(self):
        user_url = reverse("user_overview", args=[self.user.username])
        request = self.factory.get("/")
        html = render_to_string("core/partials/post_row.html", {"post": self.post}, request=request)
        self.assertIn(f'href="{user_url}"', html)

    def test_feed_card_thumbnail_links_to_content_url(self):
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Link",
            content_url="https://example.com/article",
        )
        post.thumbnail_url = "https://example.com/thumb.jpg"
        request = self.factory.get("/")
        html = render_to_string("partials/feed_card.html", {"post": post}, request=request)
        detail_url = post.get_absolute_url()
        self.assertIn(
            f'href="{post.content_url}" target="_blank" rel="noopener noreferrer"',
            html,
        )
        self.assertNotIn(f'href="{detail_url}" class="thumb"', html)
        self.assertIn(f'href="{detail_url}"', html)
        self.assertIn(f'href="{detail_url}#comments"', html)

    def test_post_row_thumbnail_links_to_content_url(self):
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="link",
            title="Link",
            content_url="https://example.com/article",
        )
        post.thumbnail_url = "https://example.com/thumb.jpg"
        request = self.factory.get("/")
        html = render_to_string("core/partials/post_row.html", {"post": post}, request=request)
        detail_url = post.get_absolute_url()
        self.assertIn(
            f'href="{post.content_url}" target="_blank" rel="noopener noreferrer" class="thumb"',
            html,
        )
        self.assertNotIn(f'href="{detail_url}" class="thumb"', html)
        self.assertIn(f'href="{detail_url}"', html)
        self.assertIn(f'href="{detail_url}#comments"', html)
