from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["post_type", "title", "body", "url"]

    def clean(self):
        cleaned_data = super().clean()

        post_type = cleaned_data.get("post_type")
        title = (cleaned_data.get("title") or "").strip()
        body = (cleaned_data.get("body") or "").strip()
        url = (cleaned_data.get("url") or "").strip()

        cleaned_data["title"] = title
        cleaned_data["body"] = body
        cleaned_data["url"] = url

        if not title:
            self.add_error("title", "Title is required.")

        if post_type == "link":
            if not url:
                self.add_error("url", "URL is required for link posts.")
            if body:
                self.add_error("body", "Body must be empty for link posts.")
        elif post_type == "text":
            if url:
                self.add_error("url", "URL must be empty for text posts.")

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
