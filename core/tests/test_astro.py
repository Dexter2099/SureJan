from datetime import datetime, timedelta, timezone as dt_timezone

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from freezegun import freeze_time

from ..models import Community, EngagementEvent, Post, CommunityBaseline
from ..services.votes import apply_vote
from ..services.astro import compute_post_signals


class AstroEngagementTests(TestCase):
    @freeze_time("2024-01-10")
    def test_vote_records_engagement_and_age(self):
        User = get_user_model()
        voter = User.objects.create_user("voter", password="pwd")
        voter.date_joined = timezone.now() - timedelta(days=7)
        voter.save()
        author = User.objects.create_user("author", password="pwd")
        community = Community.objects.create(
            slug="c", name="Comm", title="Comm", created_by=author
        )
        post = Post.objects.create(
            community=community, author=author, post_type="text", title="Hello"
        )
        delta, old, new = apply_vote(voter, "post", post.pk, 1)
        self.assertEqual(delta, 1)
        event = EngagementEvent.objects.latest("id")
        self.assertEqual(event.voter_age_days, 7)
        # removing the vote should record another event with age preserved
        delta, old, new = apply_vote(voter, "post", post.pk, 1)
        self.assertEqual(delta, -1)
        event2 = EngagementEvent.objects.latest("id")
        self.assertEqual(event2.voter_age_days, 7)

    @freeze_time("2024-02-01 00:00:00")
    def test_ring_buffer_window_and_total(self):
        User = get_user_model()
        author = User.objects.create_user("author", password="pwd")
        community = Community.objects.create(
            slug="c", name="Comm", title="Comm", created_by=author
        )
        base = datetime(2024, 2, 1, 0, 0, 0, tzinfo=dt_timezone.utc)
        with freeze_time(base):
            post = Post.objects.create(
                community=community, author=author, post_type="text", title="Hello"
            )
        for i in range(6):
            with freeze_time(base + timedelta(minutes=i)):
                voter = User.objects.create_user(f"u{i}", password="pwd")
                apply_vote(voter, "post", post.pk, 1)
        burst = post.burst_state
        self.assertEqual(len(burst.buckets), 10)
        self.assertEqual(burst.total_5m, 5)


class AstroBaselineTests(TestCase):
    @freeze_time("2024-01-31")
    def test_baseline_percentiles(self):
        User = get_user_model()
        author = User.objects.create_user("author", password="pwd")
        community = Community.objects.create(
            slug="c", name="Comm", title="Comm", created_by=author
        )
        post_time = datetime(2024, 1, 30, 0, 0, 0, tzinfo=dt_timezone.utc)
        for i in range(1, 6):
            with freeze_time(post_time):
                post = Post.objects.create(
                    community=community,
                    author=author,
                    post_type="text",
                    title=f"P{i}",
                )
            for j in range(i):
                with freeze_time(post_time + timedelta(minutes=j)):
                    EngagementEvent.objects.create(post=post, event_type="vote")
            for j in range(i - 1):
                with freeze_time(post_time + timedelta(minutes=10, seconds=j)):
                    EngagementEvent.objects.create(post=post, event_type="comment")
        call_command("compute_astro_baselines")
        baseline = CommunityBaseline.objects.get(community=community)
        self.assertAlmostEqual(baseline.p95_votes_5m, 4.8)
        self.assertAlmostEqual(baseline.p95_votes_15m, 4.8)
        self.assertAlmostEqual(baseline.p10_comments_per_100_upvotes, 20.0)


@override_settings(
    ASTRO_EARLY_VOTES_N=5,
    ASTRO_MIN_EARLY_VOTES=3,
    ASTRO_EARLY_SHARE_RED=0.5,
)
class AstroSignalFlagTests(TestCase):
    def test_compute_post_signals_flags(self):
        User = get_user_model()
        author = User.objects.create_user("author", password="pwd")
        community = Community.objects.create(
            slug="c", name="Comm", title="Comm", created_by=author
        )
        CommunityBaseline.objects.create(
            community=community,
            p95_votes_5m=2,
            p95_votes_15m=3,
            p10_comments_per_100_upvotes=50,
        )
        base = datetime(2024, 3, 1, 0, 0, 0, tzinfo=dt_timezone.utc)
        with freeze_time(base):
            post = Post.objects.create(
                community=community, author=author, post_type="text", title="Hello"
            )
        new_voters = []
        for i in range(3):
            user = User.objects.create_user(f"n{i}", password="pwd")
            user.date_joined = base - timedelta(days=1)
            user.save()
            new_voters.append(user)
        old = User.objects.create_user("old", password="pwd")
        old.date_joined = base - timedelta(days=10)
        old.save()
        times = [0, 1, 2, 10]
        voters = new_voters + [old]
        for t, voter in zip(times, voters):
            with freeze_time(base + timedelta(minutes=t)):
                apply_vote(voter, "post", post.pk, 1)
        signals = compute_post_signals(post.pk)
        flags = signals["flags"]
        self.assertTrue(flags["unusual_5"])
        self.assertTrue(flags["unusual_15"])
        self.assertTrue(flags["new_share_red"])
        self.assertTrue(flags["discuss_low"])


class AstroEndpointTests(TestCase):
    @override_settings(ASTRO_EARLY_VOTES_N=5, ASTRO_MIN_EARLY_VOTES=3)
    @freeze_time("2024-04-01 00:00:00")
    def test_json_and_chips_endpoints_feature_flag(self):
        User = get_user_model()
        author = User.objects.create_user("author", password="pwd")
        voter = User.objects.create_user("voter", password="pwd")
        community = Community.objects.create(
            slug="c", name="Comm", title="Comm", created_by=author
        )
        with freeze_time("2024-04-01 00:00:00"):
            post = Post.objects.create(
                community=community, author=author, post_type="text", title="Hello"
            )
        apply_vote(voter, "post", post.pk, 1)
        url_json = reverse("post_signals_json", args=[post.pk])
        url_chips = reverse("post_signals_chips", args=[post.pk])
        resp = self.client.get(url_json)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("rate5", resp.json())
        resp = self.client.get(url_chips)
        self.assertContains(resp, "post-context-chips")
        with override_settings(ASTROTURF_WATCH=False):
            resp = self.client.get(url_json)
            self.assertEqual(resp.status_code, 404)
            resp = self.client.get(url_chips)
            self.assertEqual(resp.status_code, 404)


class AstroFeatureFlagViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user("author", password="pwd")
        self.community = Community.objects.create(
            slug="c", name="Comm", title="Comm", created_by=self.author
        )
        self.post = Post.objects.create(
            community=self.community, author=self.author, post_type="text", title="Hello"
        )

    def test_transparency_views_respect_flag(self):
        url_methods = reverse("transparency_methods")
        url_posts = reverse("transparency_posts")
        self.assertEqual(self.client.get(url_methods).status_code, 200)
        self.assertEqual(self.client.get(url_posts).status_code, 200)
        with override_settings(ASTROTURF_WATCH=False):
            self.assertEqual(self.client.get(url_methods).status_code, 404)
            self.assertEqual(self.client.get(url_posts).status_code, 404)

    def test_chip_containers_hidden_when_flag_disabled(self):
        chips_url = reverse("post_signals_chips", args=[self.post.pk])
        detail_url = reverse(
            "post_detail",
            args=[self.community.slug, self.post.pk, slugify(self.post.title)],
        )
        self.assertContains(self.client.get(detail_url), chips_url)
        self.assertContains(self.client.get(reverse("home")), chips_url)
        with override_settings(ASTROTURF_WATCH=False):
            self.assertNotContains(self.client.get(detail_url), chips_url)
            self.assertNotContains(self.client.get(reverse("home")), chips_url)
