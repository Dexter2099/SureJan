"""Smoke test for required UI contract hooks."""

from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import NoReverseMatch, reverse


class Command(BaseCommand):
    """Verify presence of critical ``data-testid`` hooks."""

    HOME_NAMES = ["home", "index", "frontpage"]
    SUBMIT_NAMES = ["submit_post", "submit", "post_submit", "new_post"]

    def _resolve(self, names, label):
        for name in names:
            try:
                return reverse(name)
            except NoReverseMatch:
                continue
        self.stdout.write(f"✗ missing URL for {label}")
        raise SystemExit(1)

    def _has(self, html, testid):
        token = f'data-testid="{testid}"'
        token_alt = f"data-testid='{testid}'"
        return token in html or token_alt in html

    def handle(self, *args, **options):
        client = Client()
        missing = []

        home_html = client.get(
            self._resolve(self.HOME_NAMES, "home"), HTTP_HOST="localhost"
        ).content.decode()
        submit_html = client.get(
            self._resolve(self.SUBMIT_NAMES, "submit"), HTTP_HOST="localhost"
        ).content.decode()

        if not self._has(home_html, "sidebar-cta"):
            missing.append("✗ missing data-testid=sidebar-cta on Home")
        if not self._has(home_html, "post-card"):
            missing.append("✗ missing data-testid=post-card on Home")
        if not self._has(submit_html, "submit-form"):
            missing.append("✗ missing data-testid=submit-form on Submit")

        if missing:
            for line in missing:
                self.stdout.write(line)
            raise SystemExit(1)

        self.stdout.write("UI contract smoke PASS")
        raise SystemExit(0)

