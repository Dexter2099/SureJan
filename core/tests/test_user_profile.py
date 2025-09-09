from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from communities.models import Community
from core.models import Post
from comments.models import Comment


class UserProfileTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("alice", password="pwd")
        self.other = User.objects.create_user("bob", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        # Create a few posts for user and one for other
        for i in range(3):
            Post.objects.create(
                community=self.community,
                author=self.user,
                post_type="text",
                title=f"post{i}",
            )
        self.other_post = Post.objects.create(
            community=self.community,
            author=self.other,
            post_type="text",
            title="other",
        )
        # Create a few comments for user and one for other
        for i in range(3):
            Comment.objects.create(
                post=self.other_post,
                author=self.user,
                body=f"comment{i}",
            )
        Comment.objects.create(
            post=self.other_post,
            author=self.other,
            body="othercomment",
        )

    def test_overview_lists_recent_activity(self):
        url = reverse("user_overview", args=[self.user.username])
        resp = self.client.get(url)
        self.assertContains(resp, f"u/{self.user.username}")
        self.assertContains(resp, "post2")
        self.assertContains(resp, "comment2")
        self.assertNotContains(resp, "othercomment")
        self.assertContains(resp, 'class="active">Overview</a>')

    def test_comments_page_lists_comments(self):
        url = reverse("user_comments", args=[self.user.username])
        resp = self.client.get(url)
        self.assertContains(resp, "comment2")
        self.assertNotContains(resp, "post2")
        self.assertNotContains(resp, "othercomment")
        self.assertContains(resp, 'class="active">Comments</a>')

    def test_submitted_page_lists_posts(self):
        url = reverse("user_submitted", args=[self.user.username])
        resp = self.client.get(url)
        self.assertContains(resp, "post2")
        self.assertNotContains(resp, "comment2")
        self.assertNotContains(resp, "other")
        self.assertContains(resp, 'class="active">Submitted</a>')

