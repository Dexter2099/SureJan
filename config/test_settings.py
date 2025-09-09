"""Test-specific Django settings."""

import os

# Mark as build phase so base settings don't require S3 configuration.
os.environ.setdefault("DJANGO_COLLECTSTATIC", "1")

from .settings import *  # noqa: F401,F403


# Use local storage backends during tests to avoid collectstatic and external services.
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

STORAGES = {
    **STORAGES,
    "staticfiles": {"BACKEND": STATICFILES_STORAGE},
    "default": {"BACKEND": DEFAULT_FILE_STORAGE},
}

MEDIA_ROOT = BASE_DIR / "test-media"

ALLOWED_HOSTS = ["*"]

