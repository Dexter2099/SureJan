from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from communities.models import Community
from core.models import Post
from comments.models import Comment


class URLNameTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("tester", password="pwd")
        self.community = Community.objects.create(
            slug="test", name="Test", title="Test", created_by=self.user
        )
        self.post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Hello",
        )
        self.comment = Comment.objects.create(
            post=self.post, author=self.user, body="Hi", path="0001"
        )

    def test_reverse_names(self):
        self.assertEqual(reverse("feed_list"), "/feed")
        self.assertEqual(reverse("post_submit"), "/submit")
        self.assertEqual(
            reverse("post_detail_id", args=[self.post.pk]),
            f"/p/{self.post.pk}",
        )
        self.assertEqual(
            reverse(
                "post_detail",
                args=[self.community.slug, self.post.pk, self.post.slug],
            ),
            f"/r/{self.community.slug}/comments/{self.post.pk}/{self.post.slug}",
        )
        self.assertEqual(reverse("comment_create"), "/comments/create")
        self.assertEqual(
            reverse("vote_post", args=[self.post.pk]),
            f"/posts/vote/{self.post.pk}/",
        )
        self.assertEqual(
            reverse("vote_comment", args=[self.comment.pk]),
            f"/comments/vote/{self.comment.pk}/",
        )
        self.assertEqual(
            reverse("community", args=[self.community.slug]),
            f"/r/{self.community.slug}/",
        )
        self.assertEqual(reverse("healthz"), "/healthz")

