# Feature: Embeds

This project renders third‑party media behind a click‑to‑play placeholder. Supported providers and their controls are below.

## Supported providers

* **YouTube**
* **Rumble**
* **Twitter / X**

## Feature flags

Embed providers are toggled via environment flags.

| Flag | Default | Description |
|------|---------|-------------|
| `ENABLE_YOUTUBE_EMBEDS` | `1` | Allow YouTube embeds and thumbnails. |
| `ENABLE_RUMBLE_EMBEDS`  | `1` | Allow Rumble embeds and thumbnails. |
| `ENABLE_TWITTER_EMBEDS` | `0` | Allow Twitter/X embeds and images. |

## Required CSP hosts

When a provider is enabled, its hosts must appear in the Content‑Security‑Policy allowlist.

* **YouTube** – `frame-src https://www.youtube-nocookie.com`, `img-src https://i.ytimg.com`
* **Rumble** – `frame-src https://rumble.com`, `img-src https://*.rumble.com`, `https://*.rumblecdn.com`, `https://*.rmbl.ws`
* **Twitter / X** – `frame-src https://platform.twitter.com`, `img-src https://*.twimg.com`
* **All** – `img-src data:` for inline SVG placeholders

## Deployment smoke test

1. Ensure all required `ENABLE_*_EMBEDS` flags are set.
2. Verify the `Content-Security-Policy` header includes the hosts above.
3. Create a post for each provider and confirm the placeholder renders.
4. Click to load the embed and check the frame displays without CSP errors.
