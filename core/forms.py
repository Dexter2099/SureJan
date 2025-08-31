from django import forms
from django.utils.text import slugify

from .models import Comment, Post, Community, validate_image_file
from .utils.link_safety import check_url_safety


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "body", "content_url", "image"]
        widgets = {"body": forms.Textarea(attrs={"data-editor": "1"})}

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image:
            try:
                validate_image_file(image)
            except forms.ValidationError as e:
                raise e
        return image

    def clean(self):
        cleaned_data = super().clean()

        title = (cleaned_data.get("title") or "").strip()
        body = (cleaned_data.get("body") or "").strip()
        content_url = (cleaned_data.get("content_url") or "").strip()

        cleaned_data["title"] = title
        cleaned_data["body"] = body
        cleaned_data["content_url"] = content_url

        if not title:
            self.add_error("title", "Title is required.")

        if not body and not content_url:
            raise forms.ValidationError("Body or URL is required.")

        if content_url and not check_url_safety(content_url):
            self.add_error("content_url", "URL flagged as unsafe.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.image:
            instance.post_type = "image"
        elif instance.content_url:
            instance.post_type = "link"
        else:
            instance.post_type = "text"
        if commit:
            instance.save()
        return instance


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
