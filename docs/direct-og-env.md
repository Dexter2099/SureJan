# Direct OpenGraph scraping flags

Three environment variables control direct OpenGraph thumbnail fetching:

- `YT_DIRECT_OG` – YouTube (default `0`)
- `RUMBLE_DIRECT_OG` – Rumble (default `1`)
- `X_DIRECT_OG` – X/Twitter (default `0`)

When set to `1`, SureJan bypasses provider-specific fallback logic and
scrapes the provider's OpenGraph metadata directly for thumbnail images.
