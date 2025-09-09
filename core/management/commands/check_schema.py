"""Validate database schema state using migrations."""

from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    """Report unapplied, ghost, or divergent migrations."""

    def handle(self, *args, **options):
        connection = connections[DEFAULT_DB_ALIAS]
        loader = MigrationLoader(connection, ignore_no_migrations=True)
        recorder = MigrationRecorder(connection)

        graph_nodes = set(loader.graph.nodes.keys())
        applied = set(recorder.applied_migrations())

        unapplied = sorted(graph_nodes - applied)
        ghost = sorted(applied - graph_nodes)
        conflicts = loader.detect_conflicts()

        problems = False

        if unapplied:
            names = ", ".join(f"{app}.{name}" for app, name in unapplied)
            self.stdout.write(f"✗ unapplied migrations: {names}")
            problems = True

        if ghost:
            names = ", ".join(f"{app}.{name}" for app, name in ghost)
            self.stdout.write(f"✗ ghost migrations: {names}")
            problems = True

        if conflicts:
            conflict_str = ", ".join(
                f"{app}: {', '.join(names)}" for app, names in conflicts.items()
            )
            self.stdout.write(f"✗ divergent migrations: {conflict_str}")
            problems = True

        if problems:
            raise SystemExit(1)

        self.stdout.write("schema PASS")
        raise SystemExit(0)
