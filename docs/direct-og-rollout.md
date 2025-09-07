# Rollout: Direct OpenGraph thumbnails

Certain providers can fetch their OpenGraph poster images directly instead of
using deterministic CDN fallbacks. Three environment variables control this
behaviour. `RUMBLE_DIRECT_OG` defaults to `1` (enabled) while the others
default to `0` (disabled):

- `YT_DIRECT_OG` – YouTube
- `RUMBLE_DIRECT_OG` – Rumble (default `1`)
- `X_DIRECT_OG` – X/Twitter

When enabled (`1`), SureJan skips URL canonicalisation and provider-specific
fallback logic for that service. Thumbnail resolution relies solely on the
provider's OpenGraph metadata and iframe embeds are disabled.

## Rollout

1. Set the desired flag(s) to `1` and deploy.
2. Run the thumbnail backfill to refresh recent posts:
   `python manage.py backfill_thumbs --limit 50 --days 3`.

## Rollback

1. Reset the flag(s) to `0` and redeploy.
2. Backfill thumbnails again if cached results need to be refreshed.
