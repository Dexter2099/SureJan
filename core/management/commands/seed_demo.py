"""Seed the database with demo content.

Usage:
    python manage.py seed_demo
"""

from __future__ import annotations

import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import Community, Post
from votes.models import Vote
from comments.models import Comment
from core.ranking import recompute_post_ranks


class Command(BaseCommand):
    """Management command to populate the database with demo data."""

    help = (
        "Seed the database with demo users, communities, posts, comments, and votes."
    )

    def handle(self, *args, **options):
        User = get_user_model()

        # Users
        user_specs = [
            ("alice", "alice@example.com"),
            ("bob", "bob@example.com"),
            ("carol", "carol@example.com"),
            ("dave", "dave@example.com"),
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
            ("news", "News", "General news"),
            ("brisbane", "Brisbane", "Local discussions"),
        ]
        communities = []
        for slug, name, description in community_specs:
            community, created = Community.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "title": name,
                    "description": description,
                    "created_by": users[0],
                },
            )
            if created:
                self.stdout.write(f"Created community {slug}")
            communities.append(community)

        posts = []
        for community in communities:
            for i in range(random.randint(10, 20)):
                author = random.choice(users)
                post_type = random.choice(["text", "link"])
                title = f"{community.slug.capitalize()} Post {i + 1}"
                body = "Sample body" if post_type == "text" else ""
                url = (
                    f"https://example.com/{community.slug}/{i + 1}"
                    if post_type == "link"
                    else ""
                )
                post = Post.objects.create(
                    community=community,
                    author=author,
                    post_type=post_type,
                    title=title,
                    body=body,
                    url=url,
                )
                posts.append(post)

                # Comments
                roots: list[Comment] = []
                for _ in range(random.randint(0, 3)):
                    c = Comment.objects.create(
                        post=post,
                        author=random.choice(users),
                        body="Sample comment",
                    )
                    roots.append(c)
                for root in roots:
                    for _ in range(random.randint(0, 2)):
                        Comment.objects.create(
                            post=post,
                            author=random.choice(users),
                            parent=root,
                            body="Sample reply",
                        )

                # Votes
                voters = random.sample(users, k=random.randint(0, len(users)))
                for voter in voters:
                    value = random.choice([1, -1])
                    Vote.objects.create(
                        user=voter,
                        target_type="post",
                        target_id=post.pk,
                        value=value,
                    )

                up = Vote.objects.filter(
                    target_type="post", target_id=post.pk, value=1
                ).count()
                down = Vote.objects.filter(
                    target_type="post", target_id=post.pk, value=-1
                ).count()
                recompute_post_ranks(post, up, down)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(users)} users, {len(communities)} communities, and {len(posts)} posts."
            )
        )

