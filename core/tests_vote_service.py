import threading

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature

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



@skipUnlessDBFeature("supports_select_for_update")
class VoteServiceConcurrencyTests(TransactionTestCase):
    def setUp(self):
        User = get_user_model()
        self.voter1 = User.objects.create_user("voter1", password="pwd")
        self.voter2 = User.objects.create_user("voter2", password="pwd")
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

    def _run_concurrent(self, func):
        barrier = threading.Barrier(2)
        errors = []

        def runner(user):
            close_old_connections()
            try:
                barrier.wait()
                func(user)
            except Exception as exc:  # pragma: no cover - surfaced in tests
                errors.append(exc)

        t1 = threading.Thread(target=runner, args=(self.voter1,))
        t2 = threading.Thread(target=runner, args=(self.voter2,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        if errors:
            raise errors[0]

    def test_concurrent_post_votes(self):
        def vote(user):
            cast_vote_post_once(user, self.post, 1)

        self._run_concurrent(vote)
        self.post.refresh_from_db()
        self.assertEqual(self.post.score, 2)

    def test_concurrent_comment_votes(self):
        def vote(user):
            cast_vote_comment_once(user, self.comment, 1)

        self._run_concurrent(vote)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.score, 2)
