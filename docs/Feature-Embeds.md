# Feature: Embeds

This project renders third‑party media behind a click‑to‑play placeholder. Supported providers and their controls are below.

## Supported providers

* **YouTube**
* **Rumble**
* **Twitter / X**

## Feature flags

Embeds are controlled via global environment flags.

| Flag | Default | Description |
|------|---------|-------------|
| `EMBEDS_ENABLED` | `0` | Allow embeds instead of simple link cards. |
| `THUMBNAILS_ONLY` | `1` | Render thumbnails without loading frames. |
| `THUMBNAIL_CACHE_SECONDS` | `3600` | Cache lifetime for thumbnails. |

## Required CSP hosts

When a provider is enabled, its hosts must appear in the Content‑Security‑Policy allowlist.

* **YouTube** – `img-src https://i.ytimg.com`
* **Rumble** – `img-src https://*.rumble.com`, `https://*.rumblecdn.com`, `https://*.rmbl.ws`
* **Twitter / X** – `img-src https://*.twimg.com`
* **All** – `img-src data:` for inline SVG placeholders

## Deployment smoke test

1. Ensure any required flags are set appropriately.
2. Verify the `Content-Security-Policy` header includes the hosts above.
3. Create a post for each provider and confirm the placeholder renders.
4. Click to load the embed and check the frame displays without CSP errors.
