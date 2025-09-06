# Policy: Video Thumbnails & Previews

**Scope:** YouTube, X, Rumble link posts.

- All outbound fetches go through the shared HTTP client (browser UA, timeouts, retries).
- Provider map (`config/provider_map.yml`) is the single source of truth for hosts + flags.
- CSP v4+ only. Directives derived from provider map; no legacy `CSP_*` settings allowed.
- Rendering:
  - Feed → static card with thumbnail + overlay, no iframe.
  - Detail → click-to-play iframe, secure attributes.
- Caching:
  - Cache successful metadata (short TTL).
  - Never cache errors; error responses return `Cache-Control: no-store`.
- Observability:
  - Structured logs `{provider, url, source, status}`.
- Drift checks must run in CI before merge.
