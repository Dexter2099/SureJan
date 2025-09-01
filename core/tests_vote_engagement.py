from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Community, EngagementEvent, Post
from .votes import apply_vote


class VoteEngagementTests(TestCase):
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

    def test_engagement_and_burst_recorded_on_net_vote(self):
        initial_events = EngagementEvent.objects.count()
        apply_vote(self.voter, "post", self.post.pk, 1)
        self.assertEqual(EngagementEvent.objects.count(), initial_events + 1)
        event = EngagementEvent.objects.latest("id")
        self.assertEqual(event.voter_age_days, 0)
        burst = self.post.burst_state
        self.assertEqual(burst.total_5m, 1)
