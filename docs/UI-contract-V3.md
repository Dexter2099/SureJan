# SureJan V3 — UI Contract (Authoritative Layout)

> **Change control:** If any UI surface in this file changes, update this doc **and** the Penpot wireframes in the same PR.

This contract defines the exact layout surfaces, element anatomy, and required selectors. It is the single source of truth for the V3 UI.

---

## 1) Pages covered
- **Main Page** `/` and **Community** `/r/<slug>/` (same grid)
- **Submit Post** `/submit/`
- **Post Detail (thread)** `/r/<community>/comments/<pk>/<slug>/` (same grid as Main)

---

## 2) Grid & breakpoints

**Desktop frame:** 1440px  
**Centered content shell:** 1024px

Inside the 1024 shell (left→right):
- **Feed:** 700px
- **Gutter:** 24px (empty)
- **Right sidebar:** 300px

**Left sidebar (Communities):** 200–240px wide, full height, placed to the **left** of the 1024 shell.

**Mobile `<768px`:**
- Single column flow: Header → Communities (collapsible or stacked list) → Feed → Right sidebar blocks → Footer.
- Keep the order functional; no fancy reflow required.

---

## 3) Header (128px tall)
- **Left:** Logo → `/` (home). No dropdown here in V3.
- **Center:** Tabs **Hot · New · Top** (visual; links to appropriate query).
- **Right:** Account block:
  - If authed: show `{username}`
  - If not: show `Login | Signup`

Required hooks:
- Header root: `data-testid="header-bar"`
- Tabs container: `id="sort-tabs"`

---

## 4) Left Sidebar — Communities
- Title text: “**Communities**”
- Static list (initial): **News**, **Brisbane**, **Politics**, **Social**
- Each item is a simple link to `/r/<slug>/`

Semantics:
- Sidebar root uses a landmark (`<aside>` is fine).
- No search box or extra widgets in V3.

---

## 5) Main content shell (center)
Applies to **Main**, **Community**, and **Post Detail**:

### 5.1 Feed (Main/Community)
**Post card anatomy** (stacked):
- **Meta line:** `r/<slug> · author · age`
- **Title:** link to Post Detail
- **Optional media preview** (image/link/video thumb) — keep small and consistent
- **Optional body preview** (for text posts; trimmed)
- **Actions:** vote (▲▼), comment count, overflow menu

Required hook on each post card root:
- `data-testid="post-card"`

---

## 6) Right Sidebar — Account & Actions
Order (top → bottom):
1) Account block  
   - `{username}` if authed  
   - `Login | Signup` if not
2) **Submit Post** (primary CTA)
3) **Anti-Astroturf** link → `/methods`

Required hooks:
- Submit CTA: `data-testid="sidebar-submit"`
- Anti-Astroturf link: `data-testid="sidebar-astro"`

No other widgets in V3.

---

## 7) Submit Post (form)
Form stack (top → bottom):
1) **Community selector** (required)
2) **Post Title** (required)
3) **Post Media** (optional: image, link, or video)
4) **Post Body** (optional)
5) **Helper note:** “Title is required. Include body **or** media.”
6) **Submit** button (primary)

Validation rule (contractual):
- Post must have **Title** and **(Body or Media)**.

Required hook:
- Form root: `data-testid="submit-form"`

No preview feature in V3 (keep it lean).

---

## 8) Post Detail (thread)
Center column (top → bottom):
1) **Post container** (full content)
   - Title (big)  
   - Meta line (community · author · age)  
   - Media (if present)  
   - Body (full text)  
   - Actions (vote, comment count, overflow)
2) **Comment input** (textarea + submit)
3) **Comments list** (flat or lightly indented; keep simple)
   - Each comment shows author, time, body, mini actions (vote, reply)

---

## 9) Spacing & tokens (non-blocking hints)
Use simple, consistent spacing:
- Base spacing: 16px
- Large spacing: 24px
- Borders: 1px neutral grey
- Text: primary `#111`, muted `#777`
- Links: `#3366cc` (visited `#551a8b`)
- Keep contrast AA or better

(If you maintain a tokens file, mirror these there; otherwise keep local to CSS.)

---

## 10) Accessibility minima
- All links/buttons must have visible text (no icon-only actions without `aria-label`).
- Color contrast AA for text and critical UI.
- Click targets ≥ 40×40 CSS px preferred (minimum 32×32).

---

## 11) Out of scope for V3 (explicit)
- Search box, global search, or filters beyond Hot/New/Top
- Rich preview toggles on Submit
- Additional right-sidebar widgets
- Complex nested comment tree styling (keep simple)
- Client-side JS frameworks; keep SSR + minimal progressive enhancement

---

## 12) File placement guidance (non-binding)
- Header markup lives in the base layout template and is shared across pages.
- Left sidebar (Communities) is a shared partial.
- Right sidebar (Account/Submit/Astro) is a shared partial.
- Feed list and Post card are partials used by Home/Community.
- Submit form is dedicated to `/submit`.
- Post Detail view reuses card styles for the OP block.

---

## 13) Acceptance checklist (visual + hooks)
- Header shows Logo (links `/`), center tabs, and account block.  
  - ✅ `data-testid="header-bar"`, ✅ `#sort-tabs`
- Left sidebar shows “Communities” and four links (News/Brisbane/Politics/Social).
- Center shell width = **1024px**; inside is **700 + 24 + 300**.
- Right sidebar has **Account → Submit Post → Anti-Astroturf** (in that order).  
  - ✅ `data-testid="sidebar-submit"`, ✅ `data-testid="sidebar-astro"`
- Feed uses **post cards** with ✅ `data-testid="post-card"`.
- Submit form enforces: Title + (Body or Media).  
  - ✅ `data-testid="submit-form"`
- Post Detail shows full post + comment input + comments list.
- Footer shows: Terms · Privacy · About.

