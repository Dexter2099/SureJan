# SureJan V3 — One-Pager (Authoritative Spec)

> **Change control:** If this spec changes, update this file and the Penpot wireframes in the same PR.

---

## Scope
- **Pages covered**
  - Main Page (feed + left/right sidebars)
  - Submit Post Page
  - Post Detail (thread view)
- **Communities supported initially**
  - News
  - Brisbane
  - Politics
  - Social

---

## Grid
- Frame width: **1440px**
- Content shell: **1024px**, centered
  - Feed: **700px**
  - Gutter: **24px**
  - Sidebar (right): **300px**
- Left sidebar: **~200–240px** for communities list
- Mobile `<768px`: single column; feed first, then sidebars stacked

---

## Header (128px tall)
- Left: **Logo → Home**
- Center: **Tabs Hot · New · Top**
- Right: **Account / Login | Signup**

---

## Left Sidebar (Communities)
- Label: *Communities*
- List of static links:
  - News
  - Brisbane
  - Politics
  - Social

---

## Right Sidebar (User / Actions)
- If logged in: `{username}`
- If not logged in: Login | Signup
- **Submit Post** (primary CTA)
- **Anti-Astroturf** link

---

## Main Page (Feed)
- Stacked **post cards** in feed column
  - Title (link to detail page)
  - Meta: community · author · time
  - Optional media (image, link, video preview)
  - Body preview (if text post)
  - Actions: vote (▲▼), comment count, menu

---

## Submit Post Page
- **Community selector** (required)
- **Post Title** (required)
- **Post Media** (optional: image, link, video)
- **Post Body** (optional if media present)
- **Submit button**
- Validation: must include a title and at least body or media

---

## Post Detail Page
- Shows one post in full (title, meta, media, body, actions)
- **Comment input box**: textarea + submit
- **Comment thread**: flat list of replies (simple layout for now)
- Each comment:
  - Author, time
  - Comment text
  - Actions: vote, reply

---

## Footer
- Simple bar with links: Terms · Privacy · About
