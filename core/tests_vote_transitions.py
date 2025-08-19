from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Comment, Community, Post, get_points
from .votes import apply_vote


class VoteTransitionTests(TestCase):
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

    def test_post_vote_transitions_update_state(self):
        apply_vote(self.voter, "post", self.post.pk, 1)
        self.post.refresh_from_db()
        self.author.profile.refresh_from_db()
        self.assertEqual(self.post.score, 1)
        self.assertGreater(self.post.hot_rank, 0)
        self.assertGreater(self.post.rising_rank, 0)
        self.assertGreater(self.post.best_rank, 0)
        self.assertEqual(self.post.controversy, 0)
        self.assertEqual(get_points(self.author), 1)

        apply_vote(self.voter, "post", self.post.pk, 1)
        self.post.refresh_from_db()
        self.author.profile.refresh_from_db()
        self.assertEqual(self.post.score, 0)
        self.assertEqual(self.post.hot_rank, 0)
        self.assertEqual(self.post.rising_rank, 0)
        self.assertEqual(self.post.best_rank, 0)
        self.assertEqual(self.post.controversy, 0)
        self.assertEqual(get_points(self.author), 0)

        apply_vote(self.voter, "post", self.post.pk, -1)
        self.post.refresh_from_db()
        self.author.profile.refresh_from_db()
        self.assertEqual(self.post.score, -1)
        self.assertLess(self.post.hot_rank, 0)
        self.assertLess(self.post.rising_rank, 0)
        self.assertEqual(self.post.best_rank, 0)
        self.assertEqual(self.post.controversy, 0)
        self.assertEqual(get_points(self.author), -1)

    def test_comment_vote_transitions_update_state(self):
        apply_vote(self.voter, "comment", self.comment.pk, 1)
        self.comment.refresh_from_db()
        self.author.profile.refresh_from_db()
        self.assertEqual(self.comment.score, 1)
        self.assertEqual(get_points(self.author), 1)

        apply_vote(self.voter, "comment", self.comment.pk, 1)
        self.comment.refresh_from_db()
        self.author.profile.refresh_from_db()
        self.assertEqual(self.comment.score, 0)
        self.assertEqual(get_points(self.author), 0)

        apply_vote(self.voter, "comment", self.comment.pk, -1)
        self.comment.refresh_from_db()
        self.author.profile.refresh_from_db()
        self.assertEqual(self.comment.score, -1)
        self.assertEqual(get_points(self.author), -1)

