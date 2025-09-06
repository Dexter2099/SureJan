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
- Opens provider in a new tab (`target="_blank"`) with `rel="noreferrer noopener"`.

## See also (authoritative sources)
- [UI Contract V3](UI-contract-V3.md)
- [UI Flow](UI-Flow.md)
- [Wireframes](wireframes/README.md)
