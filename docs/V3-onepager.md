# SureJan V3 — One-Pager (Authoritative Spec)

> **Change control:** If this spec changes, update this file and the Penpot wireframes in the same PR.

## Scope
- Pages: Main, Submit Post, Post Detail
- Communities: News, Brisbane, Politics, Social

## Grid
- Frame: 1440px
- Content shell: 1024px centered (Feed 700 + Gutter 24 + Sidebar 300)
- Left sidebar: ~200–240px Communities list
- Mobile <768px: single column (feed → sidebars)

## Header (128px)
- Left: Logo → Home
- Center: Hot · New · Top tabs
- Right: Account/Login

## Left Sidebar
- Label: Communities
- Links: News, Brisbane, Politics, Social

## Right Sidebar
- Account/Login
- Submit Post (CTA)
- Anti-Astroturf

## Main Feed
- Post card: title, meta, body preview, actions
- Title links to `/r/<c>/comments/<id>/<slug>/`

## Submit Post
- Community selector (required)
- Title (required)
- Media (optional)
- Body (optional if media present)
- Submit button
- Validation: Title + (Body or Media)

## Post Detail
- Full post: title/meta, body, actions
- Comment input
- Comment list (flat, simple)

## Footer
- Terms · Privacy · About

