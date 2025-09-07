# Rumble thumbnail caching

SureJan downloads poster images for Rumble links and stores them under
`MEDIA_ROOT/thumbs/` to avoid hotlinking `sp.rmbl.ws`.

## Configuration

* Set `RUMBLE_DIRECT_OG=1` to fetch Rumble's OpenGraph thumbnails directly.
  The fallback CDN thumbnail is cached in the same location.
* Ensure `MEDIA_ROOT` and `MEDIA_URL` are configured to serve media files.
  `THUMB_CACHE_DIR` controls the cache directory and defaults to
  `MEDIA_ROOT/thumbs`.

Run `python manage.py backfill_thumbs` to populate thumbnails for recent
posts after enabling the feature.
