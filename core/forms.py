from django import forms
from django.utils.text import slugify

from .models import Comment, Post, Community, validate_image_file
from .utils.link_safety import check_url_safety


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["post_type", "title", "body", "url", "image"]

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

        post_type = cleaned_data.get("post_type")
        title = (cleaned_data.get("title") or "").strip()
        body = (cleaned_data.get("body") or "").strip()
        url = (cleaned_data.get("url") or "").strip()
        image = cleaned_data.get("image")

        cleaned_data["title"] = title
        cleaned_data["body"] = body
        cleaned_data["url"] = url

        if not title:
            self.add_error("title", "Title is required.")

        if post_type == "link":
            if not url:
                self.add_error("url", "URL is required for link posts.")
            else:
                if not check_url_safety(url):
                    self.add_error("url", "URL flagged as unsafe.")
            if body:
                self.add_error("body", "Body must be empty for link posts.")
            if image:
                self.add_error("image", "Image must be empty for link posts.")
        elif post_type == "text":
            if url:
                self.add_error("url", "URL must be empty for text posts.")
            if image:
                self.add_error("image", "Image must be empty for text posts.")
        elif post_type == "image":
            if not image:
                self.add_error("image", "Image is required for image posts.")
            if url:
                self.add_error("url", "URL must be empty for image posts.")
            if body:
                self.add_error("body", "Body must be empty for image posts.")

        return cleaned_data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3})}

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
