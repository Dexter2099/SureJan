# Runbook — Boot (no schema changes)

1) Ensure secrets: `DJANGO_SECRET_KEY`, `DATABASE_URL`, `MEDIA_URL`.
2) `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` only `surejan.app`.
3) `python manage.py collectstatic --noinput`
4) `python manage.py check && python manage.py runserver`
5) Verify `/healthz` → 200; `/` renders; error pages load.

