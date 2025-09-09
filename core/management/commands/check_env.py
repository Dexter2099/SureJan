"""Validate required runtime environment variables."""

import os
from urllib.parse import urlparse

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Check critical environment variables for CI."""

    def handle(self, *args, **options):
        issues = []

        if not os.environ.get("DJANGO_SECRET_KEY"):
            issues.append("missing DJANGO_SECRET_KEY")
        if not os.environ.get("DATABASE_URL"):
            issues.append("missing DATABASE_URL")

        media_url = os.environ.get("MEDIA_URL")
        if not media_url:
            issues.append("missing MEDIA_URL")
        else:
            parsed = urlparse(media_url)
            if parsed.scheme != "https":
                issues.append("MEDIA_URL not https")
            if not media_url.endswith("/"):
                issues.append("MEDIA_URL must end with /")

        if issues:
            for issue in issues:
                self.stdout.write(f"✗ {issue}")
            raise SystemExit(1)

        self.stdout.write("env PASS")
        raise SystemExit(0)
