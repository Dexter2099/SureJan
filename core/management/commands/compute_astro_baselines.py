from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from math import floor, ceil

from core.models import (
    Community,
    Post,
    EngagementEvent,
    CommunityBaseline,
)


def percentile(data, pct):
    if not data:
        return 0
    data = sorted(data)
    k = (len(data) - 1) * pct / 100.0
    f = floor(k)
    c = ceil(k)
    if f == c:
        return data[int(k)]
    d0 = data[f] * (c - k)
    d1 = data[c] * (k - f)
    return d0 + d1


class Command(BaseCommand):
    help = "Compute baseline engagement metrics for each community"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)

    def handle(self, *args, **options):
        days = options["days"]
        since = timezone.now() - timedelta(days=days)

        for community in Community.objects.all():
            posts = (
                Post.objects.filter(community=community, created_at__gte=since)
                .prefetch_related("engagement_events")
            )

            votes_5m = []
            votes_15m = []
            comment_rates = []

            for post in posts:
                five = post.created_at + timedelta(minutes=5)
                fifteen = post.created_at + timedelta(minutes=15)

                v5 = 0
                v15 = 0
                total_votes = 0
                total_comments = 0
                for e in post.engagement_events.all():
                    if e.event_type == "vote":
                        total_votes += 1
                        if e.created_at <= five:
                            v5 += 1
                        if e.created_at <= fifteen:
                            v15 += 1
                    elif e.event_type == "comment":
                        total_comments += 1
                votes_5m.append(v5)
                votes_15m.append(v15)
                if total_votes > 0:
                    comment_rates.append((total_comments * 100.0) / total_votes)

            p95_5 = percentile(votes_5m, 95)
            p95_15 = percentile(votes_15m, 95)
            p10_comments = percentile(comment_rates, 10)

            CommunityBaseline.objects.update_or_create(
                community=community,
                defaults={
                    "p95_votes_5m": p95_5,
                    "p95_votes_15m": p95_15,
                    "p10_comments_per_100_upvotes": p10_comments,
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated baseline for {community.slug}: "
                    f"5m={p95_5} 15m={p95_15} comments/100u={p10_comments}"
                )
            )

        self.stdout.write(self.style.SUCCESS("Baselines computed"))
