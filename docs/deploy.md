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

Embeds are globally controlled via environment variables:

* `EMBEDS_ENABLED` (default `0`)
* `THUMBNAILS_ONLY` (default `1`)
* `THUMBNAIL_CACHE_SECONDS` (default `3600`)

Production defaults in `fly.toml` set `EMBEDS_ENABLED=0` to disable embeds.

### CSP / Hosts

Define public domains with `DJANGO_ALLOWED_HOSTS` (comma-separated) so Django
and the CSP allowlist match your deployment URLs. Additional trusted origins
for form posts can be added with `DJANGO_CSRF_TRUSTED`.

The production CSP restricts external media to a small, documented set:

* `https://i.ytimg.com` – YouTube thumbnails.
* `https://*.twimg.com` – images in tweet thumbnails.
* `https://*.rumblecdn.com`, `https://*.rumble.com`, and `https://*.rmbl.ws` – Rumble thumbnails.
* `data:` – inline SVG placeholders.

Frames inherit `default-src 'self'`; no external origins are allowed.

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

### Link thumbnails

OpenGraph images are fetched with a browser-like User-Agent and
`Accept-Language` header. Requests timeout after roughly 4 s and each fetch
logs the provider domain, HTTP status, and whether an image URL or SVG
placeholder was returned.

Run the backfill command periodically (cron or CI) to populate thumbnails for
recent link posts:

```
flyctl ssh console -a surejan -C "python manage.py backfill_thumbs --limit 50 --days 3"
```

The command fetches provider poster or OpenGraph images asynchronously with
short timeouts and caches results before saving `thumbnail_url` and
`thumbnail_alt` on each `Post`.

## Smoke checklist

* `/accounts/signup/` → create user, header shows username.
* `/r/news/` → "Submit" visible (logged-in), post appears in feed.
* Vote/comment work; anonymous users get redirected to login for writes.
* `/secret-admin/` → admin login loads (only from allowlisted IPs if set).

### AstroShield scheduler (minimal)
Run hourly (cron or CI runner) to refresh `astro_score:*` and
`astro_band:*` cache keys:
flyctl ssh console -a surejan -C "python manage.py astro_recompute"

