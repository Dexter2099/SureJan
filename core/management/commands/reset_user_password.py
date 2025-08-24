from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Reset a user's password (emergency). Usage: manage.py reset_user_password <username> <new_password>"

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("password")

    def handle(self, *args, **opts):
        U = get_user_model()
        try:
            u = U.objects.get(username=opts["username"])
        except U.DoesNotExist:
            raise CommandError("User not found")
        u.set_password(opts["password"])
        u.save()
        self.stdout.write(self.style.SUCCESS(f"Password updated for {u.username}"))
