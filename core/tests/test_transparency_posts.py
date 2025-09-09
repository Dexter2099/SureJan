from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from communities.models import Community
from core.models import Post
from votes.services import cast_vote_post_once


@override_settings(ASTRO_EARLY_VOTES_N=5, ASTRO_MIN_EARLY_VOTES=3, ASTRO_EARLY_SHARE_RED=0.5)
class TransparencyPostsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user("author", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.author
        )

    def _new_user(self, name):
        User = get_user_model()
        return User.objects.create_user(name, password="pwd")

    def test_lists_only_flagged_posts(self):
        flagged = Post.objects.create(
            community=self.community, author=self.author, post_type="text", title="Flagged"
        )
        for i in range(3):
            voter = self._new_user(f"u{i}")
            cast_vote_post_once(voter, flagged, 1)

        old_user = self._new_user("old")
        old_user.date_joined -= timedelta(days=10)
        old_user.save()
        ok = Post.objects.create(
            community=self.community, author=self.author, post_type="text", title="OK"
        )
        cast_vote_post_once(old_user, ok, 1)

        url = reverse("transparency_posts")
        resp = self.client.get(url)
        self.assertContains(resp, "Flagged")
        self.assertNotContains(resp, "OK")
