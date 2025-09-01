from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .forms import PostForm
from .models import Community


def make_image():
    img = Image.new("RGB", (1, 1), "white")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return SimpleUploadedFile("test.jpg", buf.getvalue(), content_type="image/jpeg")


class PostFormValidationTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=user
        )

    def test_title_only_rejected(self):
        form = PostForm(data={"community": self.community.id, "title": "T"})
        self.assertFalse(form.is_valid())

    def test_body_only_allowed(self):
        form = PostForm(
            data={
                "community": self.community.id,
                "title": "T",
                "body": "B",
            }
        )
        self.assertTrue(form.is_valid())

    def test_media_with_caption_allowed(self):
        image = make_image()
        form = PostForm(
            data={
                "community": self.community.id,
                "title": "T",
                "caption": "C",
            },
            files={"media": image},
        )
        self.assertTrue(form.is_valid())

    def test_link_only_allowed(self):
        form = PostForm(
            data={
                "community": self.community.id,
                "title": "T",
                "link": "http://example.com",
            }
        )
        self.assertTrue(form.is_valid())

    def test_image_urls_allowed(self):
        urls = "\n".join(f"http://ex.com/{i}.jpg" for i in range(3))
        form = PostForm(
            data={
                "community": self.community.id,
                "title": "T",
                "image_urls": urls,
                "caption": "C",
            }
        )
        self.assertTrue(form.is_valid())

    def test_image_urls_limit(self):
        urls = "\n".join(f"http://ex.com/{i}.jpg" for i in range(6))
        form = PostForm(
            data={
                "community": self.community.id,
                "title": "T",
                "image_urls": urls,
            }
        )
        self.assertFalse(form.is_valid())
