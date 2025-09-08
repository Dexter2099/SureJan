from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from core.models import Community, Post, Comment, Vote


class VoteModelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.voter = User.objects.create_user("voter", password="pwd")
        self.author = User.objects.create_user("author", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.author
        )
        self.post = Post.objects.create(
            community=self.community, author=self.author, post_type="text", title="Hello"
        )
        self.comment = Comment.objects.create(
            post=self.post, author=self.author, body="Hi"
        )

    def test_unique_vote_per_post(self):
        Vote.objects.create(
            user=self.voter, target_type="post", target_id=self.post.pk, value=1
        )
        with self.assertRaises(IntegrityError):
            Vote.objects.create(
                user=self.voter, target_type="post", target_id=self.post.pk, value=-1
            )

    def test_unique_vote_per_comment(self):
        Vote.objects.create(
            user=self.voter, target_type="comment", target_id=self.comment.pk, value=1
        )
        with self.assertRaises(IntegrityError):
            Vote.objects.create(
                user=self.voter, target_type="comment", target_id=self.comment.pk, value=-1
            )
