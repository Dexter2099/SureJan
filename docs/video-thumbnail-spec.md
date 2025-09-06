# Feature Spec: Video Thumbnails & Previews (YouTube, X, Rumble)

## Goal
Link posts from YouTube, X (Twitter), and Rumble show a reliable thumbnail and safe preview card in the feed, with click-to-play embeds on the detail page.
---
## Steps
1. **Unified Fetching** – all oEmbed + OG scrapes use a single HTTP client with browser-like UA, retries, and timeouts.
2. **Provider Map** – one settings dict for YouTube/X/Rumble (img_hosts, frame_hosts), gated by ENABLE_* flags.
3. **CSP v4+** – compute img-src and frame-src from the provider map; remove legacy keys.
4. **Thumbnail Priority** – oEmbed thumbnail_url → provider default → OG image → fallback SVG.
5. **Rendering** – feed shows card with thumbnail + play overlay; detail page lazy-loads iframe.
6. **Cache & Headers** – cache successful results; don’t cache errors; set Cache-Control: no-store for error responses.
7. **Validation** – run manage.py check --deploy locally; smoke-test one link per provider; ensure no CSP errors in console.
