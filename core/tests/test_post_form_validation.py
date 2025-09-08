from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from core.forms import PostForm
from core.models import Community


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

    def test_image_with_caption_allowed(self):
        image = make_image()
        form = PostForm(
            data={
                "community": self.community.id,
                "title": "T",
                "body": "C",
                "post_type": "image",
            },
            files={"image": image},
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

    def test_multiple_files_rejected(self):
        files = [make_image(), make_image()]
        form = PostForm(
            data={
                "community": self.community.id,
                "title": "T",
                "post_type": "image",
            },
            files={"image": files},
        )
        self.assertFalse(form.is_valid())

    def test_size_limit(self):
        big = SimpleUploadedFile(
            "big.jpg", b"0" * (4 * 1024 * 1024 + 1), content_type="image/jpeg"
        )
        form = PostForm(
            data={
                "community": self.community.id,
                "title": "T",
                "post_type": "image",
            },
            files={"image": big},
        )
        self.assertFalse(form.is_valid())
