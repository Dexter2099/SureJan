# Flow — Create Comment

- Entry: `POST /p/<id>/comment` (Auth required)
- Validate → INSERT `core_comment` → 302 to post (or HTMX 200 fragment)
- Invariants: comments belong to a post; soft-delete hides content.

