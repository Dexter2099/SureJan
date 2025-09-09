from django import forms
from django.core.validators import MaxLengthValidator
from django.utils.text import slugify

from .models import Community


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
            raise forms.ValidationError(
                "Community with this slug already exists."
            )
        return slug

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        if name is not None:
            name = name.strip()
            if Community.objects.filter(name__iexact=name).exists():
                self.add_error(
                    "name", "Community with this name already exists."
                )
            cleaned_data["name"] = name
        return cleaned_data

