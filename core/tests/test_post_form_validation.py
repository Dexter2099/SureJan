from django.contrib.auth import get_user_model
from django.test import TestCase

from core.forms import PostForm
from core.models import Community


class PostFormValidationTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=user
        )

    def test_title_only_rejected(self):
        form = PostForm(
            data={"community": self.community.id, "title": "T", "post_type": "text"}
        )
        self.assertFalse(form.is_valid())

    def test_text_post_valid(self):
        form = PostForm(
            data={
                "community": self.community.id,
                "title": "T",
                "body": "B",
                "post_type": "text",
            }
        )
        self.assertTrue(form.is_valid())

    def test_link_only_allowed(self):
        form = PostForm(
            data={
                "community": self.community.id,
                "title": "T",
                "content_url": "http://example.com",
                "post_type": "link",
            }
        )
        self.assertTrue(form.is_valid())
