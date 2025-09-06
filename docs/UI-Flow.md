# SureJan V3 — UI Flow Map

*A living, persistent map of how a user moves through the forum UI. Use this to align code, tests, and copy.*

---

## Legend & conventions

* **Screens** are bolded; **routes** are inline code.
* **Params** show accepted query keys so we can keep links stable.
*

---

## Primary screens & routes

### 1) **Home feed**

**Route:** `/`
**Query:** `sort=hot|new|top` · `t=24h|7d|all` (only when `sort=top`) · `page=n`

**Key UI:**

* Header logo (home), centered sort tabs (Hot · New · Top)
* Post cards: community link, author link, timeago, static thumbnail (click → provider in new tab), title (link → `/r/<c>/comments/<id>/<slug>/`), excerpt, vote snippet, comments count

### 2) **Community feed**

**Route:** `/r/<slug>/`
**Query:** `sort=hot|new|top` · `t=24h|7d|all` · `page=n`

**Key UI:**

* H1 community title, same sort tabs semantics as home
* Post cards: community link, author link, timeago, static thumbnail (click → provider in new tab), title (link → `/r/<c>/comments/<id>/<slug>/`), excerpt, vote snippet, comments count

### 3) **Post detail**

**Route:** `/r/<community>/comments/<id>/<slug>/` *(canonical)* · **Alt:** `/p/<id>/`
**Query (comments):** `c_sort=best|top|new|controversial` · `q=<search>`

**Key UI:**

* Title (H1)
* Meta: **by** {username} **in** {community} · {timeago}
* **Media priority:** gallery → uploaded image → static thumbnail (YouTube/Rumble/X; click opens provider in new tab) → plain link
* Body (optional; require media **or** body)
* **Actions row:** ▲ score ▼ · **Astro chip** (green/amber/red)
* **Comment composer:** empty box + Cancel/Comment buttons (auth-gated)
* **Comment thread:** Reddit-like tree; each row has meta (author · timeago · score · optional astro chip), body, and inline actions (▲ ▼ Reply)

### 4) **Submit post**

**Route:** `/submit/`
**Fields:** Title · Body (optional) · Link URL (optional) · Images (≤5)
**Rule:** must have **either** media **or** body

### 5) **Auth**

**Routes:** `/accounts/login/` · `/accounts/signup/` · `/accounts/logout/`

### 6) **Moderation & transparency**

**Routes:** `/mod/astro/` (moderator list) · `/methods/` (public write-up) · `/transparency/posts`

---

## User journeys (happy paths)

### A) Browsing as a guest

1. **Home feed** → click a **community** (e.g., `r/brisbane`) → **Community feed**
2. Click a **post title** → **Post detail** (`/r/<c>/comments/<id>/<slug>/`)
3. Click the **thumbnail** → provider opens in new tab
4. Attempt to **comment** → redirect to **Login** → back to **Post detail** after auth

### B) Engaging as an authenticated user

1. **Home**/**Community** → vote on cards; click title to **Post detail** (`/r/<c>/comments/<id>/<slug>/`); click thumbnail → provider opens in new tab
2. In **Post detail**: static thumbnail at top; clicking opens provider in new tab; body below; actions row includes astro chip
3. **Comment:** write + submit; thread updates; reply at any depth

### C) Submitting content

1. From right sidebar (or header on mobile) → **Submit post**
2. Provide **media or body** (required rule); submit → redirect to **Post detail**

---

## Flow diagrams (Mermaid)

```mermaid
flowchart LR
  A[Home /] -->|click community| B[Community /r/<slug>/]
  A -->|click post title| C[Post detail /r/<c>/comments/<id>/<slug>/]
  A -->|click thumbnail| X[Provider site (new tab)]
  B -->|click post title| C
  B -->|click thumbnail| X
  C -->|click thumbnail| X
  C -->|comment (guest)| D[Login /accounts/login/]
  D -->|success| C
  C -->|submit comment| C
  A -->|submit post| E[Submit /submit/]
  E -->|success| C
```

```mermaid
flowchart TB
  subgraph PostDetail
    P1[Title + meta]
    P2[Media: gallery→image→static thumbnail]
    P3[Body (optional)]
    P4[Actions: ▲ score ▼ + Astro chip]
    P5[Composer]
    P6[Thread: nested comments]
    P1 --> P2 --> P3 --> P4 --> P5 --> P6
    P2 --> L[Provider opens in new tab]
  end
```

---

## Comment tree contract (UI)

* **Row meta:** author link · timeago · score · (optional) astro chip
* **Body:** rendered HTML or linebreaks; safe
* **Actions:** ▲ ▼ Reply (one line)
* **Nesting:** recursive include with `depth` (indent each level); children container appears after actions

---

## Image preview contract (feeds)

* **Preview:** if `image_thumb` present, show that; **else** show `image`
* **If neither:** (optional) use first `PostImageLink` if available
* **Thumb framing:** `aspect-ratio: 16/9; object-fit: cover; border-radius: 12px`
* **Click:** thumbnail opens provider in new tab; title links to `/r/<c>/comments/<id>/<slug>/`

---

## Route & params reference

* `/` → `sort`, `t` (only for `sort=top`), `page`
* `/r/<slug>/` → same as home
* `/r/<c>/comments/<id>/<slug>/` → `c_sort`, `q`
* `/p/<id>/` → no query required
* `/submit/` → none
* `/accounts/login|signup/` → none
* `/mod/astro/` → none; staff only
* `/methods/` → none

---

## Test hooks (recommended selectors)

* Header bar: `data-testid="header-bar"`
* Post card: `data-testid="post-card"`
* Sidebar CTA: `data-testid="sidebar-submit"`
* Astro chip: `.astro-chip` with classes `green|amber|red`
* Comment composer exists on detail when authed; absent for guests

---

## Open items / iteration notes

* Decide canonical community prefix (`/r/` vs `/c/`) and update all URL tags accordingly
* Confirm comment sort/search query names (`c_sort`, `q`)
* Decide whether to fall back to first `PostImageLink` in feeds when no upload/thumbnail exists

---

## Changelog

* v3.0 (today): initial sitemap, flows, comment contract, preview contract, routes & selectors
* (append entries as flows change)

## See also (authoritative sources)
- [Video thumbnail spec](video-thumbnail-spec.md)
- [UI Contract V3](UI-contract-V3.md)
- [Wireframes](wireframes/README.md)

