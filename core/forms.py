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
    image_urls = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"placeholder": "One image URL per line", "rows": 3}
        ),
    )

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
        image_urls_raw = (cleaned.get("image_urls") or "").strip()
        heading = (cleaned.get("heading") or "").strip()
        media = cleaned.get("media")

        # Normalize and validate image URLs
        urls = [u.strip() for u in image_urls_raw.splitlines() if u.strip()]
        if len(urls) > 5:
            self.add_error("image_urls", "A maximum of five image URLs is allowed.")
        for u in urls:
            if not check_url_safety(u):
                self.add_error("image_urls", "One or more image URLs are flagged as unsafe.")
                break

        cleaned.update(
            {
                "title": title,
                "body": body,
                "caption": caption,
                "link": link,
                "heading": heading,
                "image_urls": urls,
            }
        )

        if not title:
            self.add_error("title", "Title is required.")

        has_media = bool(media or link or urls)
        if not body and not has_media:
            raise forms.ValidationError("Provide body text or media.")

        if caption and not (media or urls):
            self.add_error("caption", "Caption requires media.")

        if link and urls:
            self.add_error("link", "Choose a link or image URLs, not both.")
            self.add_error("image_urls", "Choose a link or image URLs, not both.")

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

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        if name is not None:
            name = name.strip()
            if Community.objects.filter(name__iexact=name).exists():
                self.add_error("name", "Community with this name already exists.")
            cleaned_data["name"] = name
        return cleaned_data
