# Deployment

## Environment

Set `SENTRY_DSN` via Fly secrets or environment variables before deploying.
The Django admin lives at `/secret-admin/`; restrict it by setting an
`ADMIN_IP_ALLOWLIST` environment variable with a comma-separated list of
allowed IPs. The app exposes `/healthz` for uptime checks; point your
monitor at this path.

### Feature flags

The `ASTROTURF_WATCH` environment variable (default `1`) controls all
astroturf-detection features. Set `ASTROTURF_WATCH=0` to hide engagement
chips and block transparency pages; related endpoints will return 404.

### Moderation

Staff can remove posts without deleting them, lock conversations, or
throttle a link's domain. Throttling cuts ranking weight in half for seven
days and is useful for spammy sources.

```bash
git add -A
git commit -m "alpha: public signup + header auth + submit CTA + seeds"
# PowerShell
$REV = (Get-Date).ToString("yyyyMMddHHmmss")
flyctl deploy -a surejan --remote-only --build-arg BUILD_REV=$REV
flyctl ssh console -a surejan -C "python manage.py migrate --noinput"
flyctl ssh console -a surejan -C "python manage.py seed_basics"
flyctl logs -a surejan | Select-String -Pattern "ERROR|Traceback|favicon|collectstatic"
```

## Smoke checklist

* `/accounts/signup/` → create user, header shows username.
* `/r/news/` → "Submit" visible (logged-in), post appears in feed.
* Vote/comment work; anonymous users get redirected to login for writes.
* `/secret-admin/` → admin login loads (only from allowlisted IPs if set).

### AstroShield scheduler (minimal)
Run hourly (cron or CI runner) to refresh `astro_score:*` and
`astro_band:*` cache keys:
flyctl ssh console -a surejan -C "python manage.py astro_recompute"

