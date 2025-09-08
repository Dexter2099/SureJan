# Migration Runbook

This runbook covers backing up the database and applying migrations for the built-in `admin` app.

## Confirm User Model

Ensure Django is configured to use Django's built-in user model:

```bash
rg AUTH_USER_MODEL config/settings.py
```
Expected output:
```
AUTH_USER_MODEL = "auth.User"
```

## Back up Database

Before making migration changes, back up the existing database.
For SQLite:

```bash
cp db.sqlite3 db_backup.sqlite3
```

## Capture Migration State

Check migration status for the `admin` app:

```bash
python manage.py showmigrations admin
```

## Apply Migrations

Run migrations:

```bash
python manage.py migrate --noinput
```

If errors persist, reset the admin app and retry:

```bash
python manage.py migrate admin zero --fake
python manage.py migrate --noinput
```

## Verify

Confirm all migrations are applied:

```bash
python manage.py migrate --plan
python manage.py showmigrations admin
```

The plan should show no pending operations and the migrations should be marked with `[X]`.

