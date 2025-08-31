from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

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
            f"/r/{self.community.slug}/comments/{self.post.pk}/{self.post.slug}/",
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        for comment in (root, child):
            self.assertContains(resp, f'id="c{comment.pk}"')
            user_url = reverse("user_overview", args=[comment.author.username])
            self.assertEqual(user_url, f"/u/{comment.author.username}/")
            self.assertContains(resp, f'href="{user_url}"')
