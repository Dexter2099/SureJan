# SureJan V3 — UI Contract (Authoritative Layout)

> **Change control:** If any UI surface in this file changes, update this doc and the Penpot wireframes in the same PR.

## Pages covered
- Main `/` + Community `/r/<slug>/`
- Submit `/submit/`
- Post Detail `/r/<community>/comments/<pk>/<slug>/`

## Grid
- Desktop: 1440 frame, 1024 shell (Feed 700 + Gutter 24 + Sidebar 300)
- Left sidebar: 200–240px
- Mobile: single column

## Header (128px)
- Left: Logo → Home
- Center: Hot · New · Top tabs
- Right: Account/Login
- Required: `data-testid="header-bar"`, `id="sort-tabs"`

## Left Sidebar
- Title: Communities
- Links: News, Brisbane, Politics, Social

## Right Sidebar
- Account/Login
- Submit Post CTA → `data-testid="sidebar-submit"`
- Anti-Astroturf → `data-testid="sidebar-astro"`

## Feed
- Post card anatomy: meta, title (links to `/r/<c>/comments/<id>/<slug>/`), optional static thumbnail (opens provider in new tab) or body, actions
- Hook: `data-testid="post-card"`

## Submit Post
- Community selector, Title, Media, Body, Submit
- Rule: Title + (Body or Media)
- Hook: `data-testid="submit-form"`

## Post Detail
- OP card: full content with static thumbnail; clicking opens provider in new tab
- Comment input
- Comments list: author/time/body/actions

## Accessibility minima
- Visible text for all actions
- AA contrast
- Min click targets 32×32

## Out of scope
- Search, advanced filters, preview toggle, extra sidebar widgets

## Acceptance checklist
- Header with logo, tabs, account
- Left sidebar with Communities
- Right sidebar with Account/Login, Submit, Astro
- Feed with `data-testid="post-card"`
- Submit form with `data-testid="submit-form"`
- Post detail shows post + comments; media is static thumbnail; clicking opens provider in new tab
- Footer: Terms · Privacy · About

## See also (authoritative sources)
- [Video thumbnail spec](video-thumbnail-spec.md)
- [UI Flow](UI-Flow.md)
- [Wireframes](wireframes/README.md)

