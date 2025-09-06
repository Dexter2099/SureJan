# Feature Spec: Video Thumbnails (YouTube, X, Rumble)

## Goal
No embeds anywhere; thumbnail card only on feed and detail.

## Thumbnail requirements
- 16:9 crop (`aspect-ratio: 16/9`)
- `object-fit: cover`
- Rounded corners
- Lazy loading
- Alt text
- Provider label

## Click behavior
- **Feed:**
  - Title → post detail.
  - Thumbnail → external provider (`target="_blank"`, `rel="noopener noreferrer"`).
- **Post detail:**
  - Thumbnail → external provider (`target="_blank"`, `rel="noopener noreferrer"`).

## Caching & timeouts
- Outbound fetches use the shared HTTP client (browser UA, timeouts, retries).
- Cache successful metadata with a short TTL; never cache errors (`Cache-Control: no-store`).
- See [UI Flow](UI-Flow.md) and [UI Contract V3](UI-contract-V3.md) for integration details.

## Acceptance hooks
- Feed cards expose `data-testid="post-card"` for V3 acceptance tests.

## See also (authoritative sources)
- [UI Contract V3](UI-contract-V3.md)
- [UI Flow](UI-Flow.md)
- [Wireframes](wireframes/README.md)
