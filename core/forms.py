from django import forms
from django.utils.text import slugify

from .models import Comment, Community, validate_image_file
from .utils.link_safety import check_url_safety


class PostForm(forms.Form):
    """Form for submitting a post."""

    community = forms.ModelChoiceField(queryset=Community.objects.all(), required=True)
    title = forms.CharField(max_length=120)
    heading = forms.CharField(max_length=80, required=False)
    body = forms.CharField(
        widget=forms.Textarea(attrs={"data-editor": "1"}), required=False
    )
    media = forms.FileField(required=False)
    caption = forms.CharField(
        widget=forms.Textarea(attrs={"data-editor": "1"}), required=False
    )
    link = forms.URLField(required=False)

    def clean_media(self):
        media = self.cleaned_data.get("media")
        if media and getattr(media, "content_type", "").startswith("image/"):
            try:
                validate_image_file(media)
            except forms.ValidationError as exc:  # pragma: no cover - defensive
                raise exc
        return media

    def clean(self):
        cleaned = super().clean()
        title = (cleaned.get("title") or "").strip()
        body = (cleaned.get("body") or "").strip()
        caption = (cleaned.get("caption") or "").strip()
        link = (cleaned.get("link") or "").strip()
        heading = (cleaned.get("heading") or "").strip()
        media = cleaned.get("media")

        cleaned.update({"title": title, "body": body, "caption": caption, "link": link, "heading": heading})

        if not title:
            self.add_error("title", "Title is required.")

        if not body and not media:
            raise forms.ValidationError("Provide body text or media.")

        if caption and not media:
            self.add_error("caption", "Caption requires media.")

        if link and not check_url_safety(link):
            self.add_error("link", "URL flagged as unsafe.")

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
