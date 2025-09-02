from django import forms
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

    POST_TYPES = [("text", "Text"), ("link", "Link"), ("images", "Images")]

    community = forms.ModelChoiceField(queryset=Community.objects.all(), required=True)
    post_type = forms.ChoiceField(choices=POST_TYPES, widget=forms.RadioSelect)
    title = forms.CharField(max_length=300)
    body = forms.CharField(
        widget=forms.Textarea(attrs={"data-editor": "1"}), required=False
    )
    link = forms.URLField(required=False)
    class MultiFileInput(forms.ClearableFileInput):
        allow_multiple_selected = True

    images = forms.FileField(required=False, widget=MultiFileInput)

    def clean_body(self):
        body = (self.cleaned_data.get("body") or "").strip()
        if not body:
            return ""
        html = markdown_renderer(body)
        return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)

    def clean_images(self):
        files = self.files.getlist("images")
        if len(files) > 5:
            raise forms.ValidationError("You can upload up to 5 images.")
        for f in files:
            if f.size > 4 * 1024 * 1024:
                raise forms.ValidationError("Image too large (max 4MB).")
            validate_image_file(f)
        return files

    def clean(self):
        cleaned = super().clean()
        title = (cleaned.get("title") or "").strip()
        link = (cleaned.get("link") or "").strip()
        post_type = cleaned.get("post_type")
        images = cleaned.get("images") or []
        body = cleaned.get("body") or ""

        cleaned.update({"title": title, "link": link, "images": images, "body": body})

        if not title:
            self.add_error("title", "Title is required.")

        if post_type == "text":
            if not body:
                self.add_error("body", "Body is required for text posts.")
        elif post_type == "link":
            if not link:
                self.add_error("link", "Link is required for link posts.")
            elif not check_url_safety(link):
                self.add_error("link", "URL flagged as unsafe.")
        elif post_type == "images":
            if not images:
                self.add_error("images", "At least one image is required.")
        else:
            self.add_error("post_type", "Invalid post type.")

        return cleaned


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "data-editor": "1"})}

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
