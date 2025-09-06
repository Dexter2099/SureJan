# Policy: Video Thumbnails

**Scope:** YouTube, X, Rumble link posts.

Feed and post detail render static thumbnails only; clicking the image opens the provider in a new tab.

## Provider map
Provider map (`config/provider_map.yml`) is the single source of truth for hosts and flags.

## Caching
All outbound fetches go through the shared HTTP client (browser UA, timeouts, retries).
Cache successful metadata with a short TTL.
Never cache errors; error responses return `Cache-Control: no-store`.

## Observability
Structured logs `{provider, url, source, status}`.

## CI drift checks
Drift checks must run in CI before merge.
