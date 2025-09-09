# Module Boundaries (current → target)

**Current:** `core/` holds models, views, forms, services, templates.

**Target (code-first split; models remain in core until stable):**
- `posts/` — views/forms/services/templates for posts.
- `comments/` — comment CRUD & moderation helpers.
- `votes/` — vote endpoints + idempotent service.
- `communities/` — community listing/admin UI.

**Public APIs**
- posts.services: `create_post`, `get_post`, `list_feed`
- comments.services: `add_comment`, `list_comments`
- votes.services: `cast_vote(user, target, value)` (value ∈ {+1, -1, 0})
- communities.services: `get_by_slug`, `list_communities`

Rule: views ↔ services ↔ models. Templates read context only.

