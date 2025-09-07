# Video Thumbnails Preview Spec

This note summarizes how we fetch and display video thumbnails in preview contexts.

- **Canonicalization**: Every incoming video URL is normalized to its canonical form before we request metadata or images. This avoids duplicate cache entries and ensures predictable lookups.
- **Headers**: Requests to providers include only the headers we control (e.g. `User-Agent`, `Accept`). Client-provided headers are not forwarded.
- **Timeouts**: Thumbnail fetches run with short connection and read timeouts so preview rendering does not block the page.
- **Retries**: Transient network failures are retried a limited number of times.
- **No retry on 403**: If a provider responds with `403 Forbidden`, we treat it as a permanent failure and do not retry.

