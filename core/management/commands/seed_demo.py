from __future__ import annotations

import random
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from core.models import Community, Post


class Command(BaseCommand):
    help = "Seed the database with demo users, communities, and posts."

    def handle(self, *args, **options):
        User = get_user_model()

        # Users
        user_specs = [
            ("alice", "alice@example.com"),
            ("bob", "bob@example.com"),
        ]
        users = []
        for username, email in user_specs:
            user, created = User.objects.get_or_create(
                username=username, defaults={"email": email}
            )
            if created:
                self.stdout.write(f"Created user {username}")
            user.set_password("pass12345!")
            user.save()
            users.append(user)

        # Communities
        community_specs = [
            ("news", "News", "Latest news"),
            ("pics", "Pics", "Photos and images"),
            ("tech", "Tech", "Technology discussions"),
        ]
        communities = []
        for name, title, description in community_specs:
            community, created = Community.objects.get_or_create(
                name=name,
                defaults={"title": title, "description": description},
            )
            if created:
                self.stdout.write(f"Created community {name}")
            communities.append(community)

        # Posts
        post_types = [pt[0] for pt in Post.POST_TYPES]
        posts = []
        for i in range(30):
            community = random.choice(communities)
            author = random.choice(users)
            post_type = random.choice(post_types)
            title = f"Post {i + 1}"
            body = ""
            url = ""
            if post_type == "text":
                body = "Sample body"
            elif post_type == "link":
                url = f"https://example.com/{i + 1}"
            post = Post.objects.create(
                community=community,
                author=author,
                post_type=post_type,
                title=title,
                body=body,
                url=url,
                score=random.randint(0, 100),
            )
            posts.append(post)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(users)} users, {len(communities)} communities, and {len(posts)} posts."
            )
        )
