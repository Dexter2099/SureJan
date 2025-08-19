from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Community, Post


class UserProfileTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("alice", password="pwd")
        self.other = User.objects.create_user("bob", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        # Create 11 posts for user and one for other
        for i in range(11):
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
        # Create 11 comments for user and one for other
        for i in range(11):
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
        # newest post and comment present, oldest omitted
        self.assertContains(resp, "post10")
        self.assertContains(resp, "comment10")
        self.assertNotContains(resp, "post0")
        self.assertNotContains(resp, "comment0")
        self.assertContains(resp, 'class="active">Overview</a>')

    def test_comments_page_lists_comments(self):
        url = reverse("user_comments", args=[self.user.username])
        resp = self.client.get(url)
        self.assertContains(resp, "comment10")
        self.assertNotContains(resp, "post10")
        self.assertNotContains(resp, "othercomment")
        self.assertContains(resp, 'class="active">Comments</a>')

    def test_submitted_page_lists_posts(self):
        url = reverse("user_submitted", args=[self.user.username])
        resp = self.client.get(url)
        self.assertContains(resp, "post10")
        self.assertNotContains(resp, "comment10")
        self.assertNotContains(resp, "other")
        self.assertContains(resp, 'class="active">Submitted</a>')

