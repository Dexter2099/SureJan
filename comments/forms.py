from django import forms
from django.core.validators import MaxLengthValidator

from .models import Comment


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
