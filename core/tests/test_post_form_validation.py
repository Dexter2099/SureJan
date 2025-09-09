from io import BytesIO
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from core.forms import PostForm
from communities.models import Community


class PostFormValidationTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=user
        )

    def _image_file(self, fmt="JPEG", name="test.jpg"):
        buffer = BytesIO()
        Image.new("RGB", (1, 1)).save(buffer, format=fmt)
        return SimpleUploadedFile(
            name,
            buffer.getvalue(),
            content_type=f"image/{fmt.lower()}",
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

    def test_image_post_requires_single_source(self):
        img = self._image_file()
        form = PostForm(
            data={
                "community": self.community.id,
                "title": "T",
                "post_type": "image",
                "content_url": "http://example.com/x.jpg",
            },
            files={"image": img},
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Choose either an image file or a content URL, not both.",
            form.errors["image"],
        )

        form = PostForm(
            data={"community": self.community.id, "title": "T", "post_type": "image"}
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Provide a JPEG/PNG file or a valid image URL.",
            form.errors["image"],
        )

    def test_image_post_valid_file(self):
        img = self._image_file()
        form = PostForm(
            data={"community": self.community.id, "title": "T", "post_type": "image"},
            files={"image": img},
        )
        self.assertTrue(form.is_valid())

    def test_image_post_invalid_type(self):
        gif = self._image_file(fmt="GIF", name="t.gif")
        form = PostForm(
            data={"community": self.community.id, "title": "T", "post_type": "image"},
            files={"image": gif},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Only JPEG/PNG are supported.", form.errors["image"])

    def test_image_post_too_large(self):
        buffer = BytesIO()
        Image.new("RGB", (1, 1)).save(buffer, format="JPEG")
        big_bytes = buffer.getvalue() + b"0" * (5 * 1024 * 1024)
        big = SimpleUploadedFile("big.jpg", big_bytes, content_type="image/jpeg")
        form = PostForm(
            data={"community": self.community.id, "title": "T", "post_type": "image"},
            files={"image": big},
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Provide a JPEG/PNG file or a valid image URL.",
            form.errors["image"],
        )

    @patch("core.forms.requests.head")
    def test_image_post_valid_content_url(self, mock_head):
        mock_head.return_value = Mock(
            headers={"Content-Type": "image/png", "Content-Length": "100"}
        )
        form = PostForm(
            data={
                "community": self.community.id,
                "title": "T",
                "post_type": "image",
                "content_url": "http://example.com/x.png",
            }
        )
        self.assertTrue(form.is_valid())
        mock_head.assert_called_once()

    @patch("core.forms.requests.head")
    def test_image_post_invalid_content_url_type(self, mock_head):
        mock_head.return_value = Mock(
            headers={"Content-Type": "text/html", "Content-Length": "100"}
        )
        form = PostForm(
            data={
                "community": self.community.id,
                "title": "T",
                "post_type": "image",
                "content_url": "http://example.com/x.png",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Only JPEG/PNG are supported.", form.errors["content_url"])
