from django import forms
from django.core.validators import (
    FileExtensionValidator,
    MaxLengthValidator,
    URLValidator,
)
from django.utils.text import slugify

import bleach
import mistune

from .models import Comment, Community, validate_image_file
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
    image = forms.ImageField(
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "gif", "webp"])
        ],
    )

    def clean_body(self):
        body = (self.cleaned_data.get("body") or "").strip()
        if not body:
            return ""
        html = markdown_renderer(body)
        return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)

    def clean_image(self):
        files = self.files.getlist("image")
        if len(files) > 1:
            raise forms.ValidationError("Only one image is allowed.")
        if files:
            f = files[0]
            if f.size > 4 * 1024 * 1024:
                raise forms.ValidationError("Image too large (max 4MB).")
            validate_image_file(f)
            return f
        return None

    def clean(self):
        cleaned = super().clean()
        title = (cleaned.get("title") or "").strip()
        content_url = (cleaned.get("content_url") or "").strip()
        post_type = cleaned.get("post_type")
        image = cleaned.get("image")
        body = cleaned.get("body") or ""

        cleaned.update(
            {
                "title": title,
                "content_url": content_url,
                "image": image,
                "body": body,
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
            if not image:
                self.add_error("image", "Image is required.")
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
