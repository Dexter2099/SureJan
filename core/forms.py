from django import forms
from django.utils.text import slugify

from .models import Comment, Post, Community, validate_image_file
from .utils.link_safety import check_url_safety


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            "community",
            "title",
            "heading",
            "post_type",
            "body",
            "content_url",
            "image",
        ]
        widgets = {"body": forms.Textarea(attrs={"data-editor": "1"})}
        help_texts = {
            "community": "Where to post.",
            "title": "Brief post title.",
            "heading": "Optional heading.",
            "post_type": "Choose text, link or image.",
            "body": "Required for text posts.",
            "content_url": "Required for link posts.",
            "image": "Required for image posts.",
        }

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
        heading = (cleaned_data.get("heading") or "").strip()
        body = (cleaned_data.get("body") or "").strip()
        content_url = (cleaned_data.get("content_url") or "").strip()
        post_type = cleaned_data.get("post_type")
        image = cleaned_data.get("image")

        cleaned_data.update(
            {
                "title": title,
                "heading": heading,
                "body": body,
                "content_url": content_url,
            }
        )

        if not title:
            self.add_error("title", "Title is required.")

        if post_type == "text":
            if not body:
                self.add_error("body", "Body required for text posts.")
        elif post_type == "link":
            if not content_url:
                self.add_error("content_url", "URL required for link posts.")
            elif content_url and not check_url_safety(content_url):
                self.add_error("content_url", "URL flagged as unsafe.")
        elif post_type == "image":
            if not image:
                self.add_error("image", "Image required for image posts.")
        else:
            raise forms.ValidationError("Invalid post type.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        post_type = self.cleaned_data.get("post_type")
        if post_type in dict(Post._meta.get_field("post_type").choices):
            instance.post_type = post_type
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
