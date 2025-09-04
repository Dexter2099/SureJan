from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Comment, Community, Post, get_points
from .services.votes import cast_vote_post_once, cast_vote_comment_once, AlreadyVoted


class VoteServiceTests(TestCase):
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

    def test_post_vote_once(self):
        cast_vote_post_once(self.voter, self.post, 1)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 1)
        self.author.profile.refresh_from_db()
        self.assertEqual(get_points(self.author), 1)
        with self.assertRaises(AlreadyVoted):
            cast_vote_post_once(self.voter, self.post, -1)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 1)
        self.author.profile.refresh_from_db()
        self.assertEqual(get_points(self.author), 1)

    def test_comment_vote_once(self):
        cast_vote_comment_once(self.voter, self.comment, -1)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.score, -1)
        self.author.profile.refresh_from_db()
        self.assertEqual(get_points(self.author), -1)
        with self.assertRaises(AlreadyVoted):
            cast_vote_comment_once(self.voter, self.comment, 1)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.score, -1)
        self.author.profile.refresh_from_db()
        self.assertEqual(get_points(self.author), -1)
