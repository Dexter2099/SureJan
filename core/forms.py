from django import forms
from django.core.validators import MaxLengthValidator, URLValidator
from django.utils.text import slugify

import os
from urllib.parse import urlparse

import bleach
import mistune
import requests
from PIL import Image

from .models import Comment, Community
from .utils.link_safety import check_url_safety


markdown_renderer = mistune.create_markdown()

ALLOWED_TAGS = [
    "p",
    "h1",
    "h2",
    "h3",
    "a",
    "strong",
    "em",
    "code",
    "pre",
    "ul",
    "ol",
    "li",
    "blockquote",
    "br",
]
ALLOWED_ATTRIBUTES = {"a": ["href"]}


class PostForm(forms.Form):
    """Form for submitting a post."""

    POST_TYPES = [("text", "Text"), ("link", "Link"), ("image", "Image")]

    community = forms.ModelChoiceField(queryset=Community.objects.all(), required=True)
    post_type = forms.ChoiceField(choices=POST_TYPES, widget=forms.RadioSelect)
    title = forms.CharField(
        max_length=140, validators=[MaxLengthValidator(140)]
    )
    body = forms.CharField(
        widget=forms.Textarea(
            attrs={"data-editor": "1", "maxlength": 10000, "data-max": 10000}
        ),
        required=False,
        validators=[MaxLengthValidator(10000)],
    )
    content_url = forms.CharField(
        max_length=2048,
        validators=[MaxLengthValidator(2048), URLValidator()],
        required=False,
    )
    image = forms.ImageField(required=False)

    def clean_body(self):
        body = (self.cleaned_data.get("body") or "").strip()
        if not body:
            return ""
        html = markdown_renderer(body)
        return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)

    def clean(self):
        cleaned = super().clean()
        title = (cleaned.get("title") or "").strip()
        content_url = (cleaned.get("content_url") or "").strip()
        post_type = cleaned.get("post_type")
        body = cleaned.get("body") or ""
        image = cleaned.get("image")

        cleaned.update(
            {
                "title": title,
                "content_url": content_url,
                "body": body,
                "image": image,
            }
        )

        if not title:
            self.add_error("title", "Title is required.")

        if post_type == "text":
            if not body:
                self.add_error("body", "Body is required for text posts.")
        elif post_type == "link":
            if not content_url:
                self.add_error("content_url", "Link is required for link posts.")
            elif not check_url_safety(content_url):
                self.add_error("content_url", "URL flagged as unsafe.")
        elif post_type == "image":
            has_image = bool(image)
            has_url = bool(content_url)
            if has_image and has_url:
                msg = "Choose either an image file or a content URL, not both."
                self.add_error("image", msg)
                self.add_error("content_url", msg)
            elif not has_image and not has_url:
                msg = "Provide a JPEG/PNG file or a valid image URL."
                self.add_error("image", msg)
                self.add_error("content_url", msg)
            elif has_image:
                if image.size > 5 * 1024 * 1024:
                    self.add_error(
                        "image", "Provide a JPEG/PNG file or a valid image URL."
                    )
                else:
                    ext = os.path.splitext(image.name)[1].lower()
                    if ext not in [".jpg", ".jpeg", ".png"]:
                        self.add_error("image", "Only JPEG/PNG are supported.")
                    else:
                        try:
                            image.file.seek(0)
                            img = Image.open(image)
                            if img.format not in ["JPEG", "PNG"]:
                                self.add_error(
                                    "image", "Only JPEG/PNG are supported."
                                )
                        except Exception:
                            self.add_error(
                                "image", "Only JPEG/PNG are supported."
                            )
            else:  # has_url
                ext = os.path.splitext(urlparse(content_url).path)[1].lower()
                if ext not in [".jpg", ".jpeg", ".png"]:
                    self.add_error("content_url", "Only JPEG/PNG are supported.")
                else:
                    try:
                        resp = requests.head(content_url, allow_redirects=True, timeout=5)
                        content_type = resp.headers.get("Content-Type", "")
                        content_length = int(resp.headers.get("Content-Length") or 0)
                        if content_type not in ["image/jpeg", "image/png"]:
                            self.add_error(
                                "content_url", "Only JPEG/PNG are supported."
                            )
                        elif content_length > 5 * 1024 * 1024:
                            self.add_error(
                                "content_url",
                                "Provide a JPEG/PNG file or a valid image URL.",
                            )
                    except Exception:
                        self.add_error(
                            "content_url", "Provide a JPEG/PNG file or a valid image URL."
                        )
        else:
            self.add_error("post_type", "Invalid post type.")

        return cleaned


class CommentForm(forms.ModelForm):
    body = forms.CharField(
        widget=forms.Textarea(
            attrs={"rows": 3, "data-editor": "1", "maxlength": 10000, "data-max": 10000}
        ),
        validators=[MaxLengthValidator(10000)],
    )

    class Meta:
        model = Comment
        fields = ["body"]

    def clean_body(self):
        body = (self.cleaned_data.get("body") or "").strip()
        if not body:
            raise forms.ValidationError("Comment cannot be empty.")
        return body


class CommunityCreateForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ["slug", "name", "title", "description"]

    def clean_slug(self):
        slug = slugify(self.cleaned_data.get("slug", ""))
        MaxLengthValidator(191)(slug)
        if not slug:
            raise forms.ValidationError("Slug is required.")
        if Community.objects.filter(slug=slug).exists():
            raise forms.ValidationError("Community with this slug already exists.")
        return slug

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        if name is not None:
            name = name.strip()
            if Community.objects.filter(name__iexact=name).exists():
                self.add_error("name", "Community with this name already exists.")
            cleaned_data["name"] = name
        return cleaned_data
