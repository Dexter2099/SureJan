# SureJan V2 — One-Pager (Authoritative Spec)

> **This document is the single source of truth for V2.**  
> If it’s not here, it’s out of scope. Any change requires updating this file in the same PR.

## 1) Purpose
Ship a small, fast, safe, **local forum** for 4 starter communities with simple posting, comments, basic voting, and first-pass anti-astroturf. V2 optimizes for reliability and clarity over features.

## 2) Scope (In / Out)
**In:**  
- 4 communities (seeded).  
- Post types: **Text**, **Link** (YouTube/Rumble/X with *click-to-play*), **Image slideshow** (≤5 images via URLs).  
- Comments, basic up/down vote.  
- Roles: Guest, Authenticated User, Mod, Admin.  
- Moderation actions: **Remove (soft)**, **Lock**, **Slowmode** (0/30/60/120s), **Domain-throttle** (ranking weight −50%).  
- Anti-astroturf **AstroShield v1**: account/post activity → score **1–100**; chip bands; slowmode auto at ≥70; `/methods` page documents signals.  
- Safety: strict **CSP allowlist**, **no third-party JS until consent**, **click-to-play** for embeds, **rate limits** (posts/day, comments/min, votes/min).  
- Server-rendered pages (works without JS).  
- Deploy on Fly.io with **Postgres (Neon OK)**, WhiteNoise static.

**Out:**  
- OAuth/Social login, rich editors, full text search, DM/notifications, appeal workflow, theming, i18n, mobile app, analytics dashboards.  
- Any embed providers beyond YouTube-nocookie/Rumble/X (behind consent).

## 3) URLs & Navigation
- `/` — Home feed (all communities).  
- `/r/<slug>` — Community feed.  
- `/p/<id>` — Post detail + comments.  
- `/submit` — Submit post.  
- `/mod/astro` — Minimal mod list (reports/notes + high-score posts).  
- `/methods` — Public write-up of AstroShield v1 and safety measures.  
**Sort:** Hot (default), New, Top(24h/7d/All).  
**Time filter:** Applied **only** when requested (`?t=24h|7d|all`).

## 4) UX & Layout (baseline)
- **Centered feed** (≈700px) with **right gutter** sidebar (300–320px) containing only: **Submit Post** (primary CTA) and **Anti-Astroturf** link.  
- Mobile: single column; submit CTA in header.  
- Post card: meta (community • author • age), clamped title, optional thumb, votes, comments, **Astro chip**.  
- Detail: safe embed card (click-to-play sandboxed iframe), image carousel (≤5), comments list + composer.

## 5) Data & Rules (light sketch)
- `Community(slug,name)`; `Post(author, community, title, body?, link_url?, images[≤5])`  
  Flags: `is_deleted(False)`, `is_removed(False)`, `is_locked(False)`, `slowmode_seconds(0)`, `domain_weight(0|−50)`  
- `Comment(author, post, body, is_removed=False)`  
- `Vote(user, {post|comment}, value∈{−1, +1})`  
- `AstroScore(object_type, object_id, score:int, band:str, signals:json, created_at)` (latest only used).  
**Visibility:** `visible = not is_deleted and not is_removed`.  
**Default feed:** no implicit time filter; order by Hot score; fall back to New.

## 6) AstroShield v1 (signals → score 1–100)
Compute on post/comment activity (≤1/120s) using:  
- **Account age** vs activity rate (posting/voting bursts).  
- **Vote rate spikes** vs P95 of site (e.g., >5/15min early life).  
- **Discuss ratio** (comments:upvotes) abnormally low.  
Map to **bands** (0–39 green, 40–69 amber, 70–100 red).  
**Actions:** show chip; apply **slowmode** automatically at ≥70; list in `/mod/astro`.  
Expose constants + rationale on `/methods`.

## 7) Moderation
- Inline: **Remove (soft)**, **Lock**, **Slowmode** (0/30/60/120), **Domain-throttle**.  
- **Report** creates ModNote (minimal).  
- Staff can always act; authors can delete their own post ≤15m (hard-delete if no comments; else soft).

## 8) Safety & Privacy
- **CSP allowlist** for embeds; if consent not given, show link-card only.  
- **Click-to-play** iframes with sandbox, referrerpolicy, and `youtube-nocookie`.  
- **Rate limits**: defaults (env-tunable) posts/day/user, comments/min/user, votes/min/user.  
- **No third-party JS until consent**; store consent in a first-party cookie.

## 9) Ops & Environments
- **Prod/Staging** are separate Fly apps and DBs.  
- **Prod must not fall back to SQLite.** `DATABASE_URL` required; abort startup if missing.  
- `release_command: python manage.py migrate --noinput`.  
- Static via WhiteNoise; `collectstatic` at build time.  
- Seed command `seed_basics` for 4 communities + 3 demo posts (for staging only).

### Required env vars
`SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CSP_EMBED_ALLOWLIST` (comma-sep), `RATE_POSTS_PER_DAY`, `RATE_COMMENTS_PER_MIN`, `RATE_VOTES_PER_MIN`, optional `SENTRY_DSN`.

## 10) Definition of Done (V2)
- Feeds render server-side with visible posts; sort & time filters behave as specified.  
- Submit supports Text/Link/Images(≤5) with friendly validation; rate limits enforced.  
- Detail page renders safe embeds/images; comments + votes work.  
- AstroShield v1 chip shows; slowmode auto at ≥70; `/methods` published.  
- Moderation actions function; Report → ModNote; author self-delete ≤15m.  
- CSP enforced; no third-party JS until consent; click-to-play embeds.  
- Staging + Prod live; migrations through `release_command`; smoke test passes; deps pinned.

## 11) Acceptance & Smoke Tests (minimal)
1. Seed staging; home `/` shows ≥1 post; invalid `?page` falls back to page 1.  
2. Submit: (a) Text-only, (b) Link (YouTube) with consent gate, (c) 3-image slideshow; all appear in feed.  
3. Rate limits: exceeding comment/vote thresholds yields friendly 429 UI.  
4. AstroShield: set a user to high-risk (fixture) → chip shows, slowmode applied.  
5. Moderation: remove/lock/slowmode/domain-throttle visibly affect feed/detail.  
6. CSP report-only check passes; no third-party JS loaded before consent.

## 12) Milestones (must merge in order)
1) Data model & migration set; seed 4 communities.  
2) Routes + base views (`/`, `/r/*`, `/p/*`, `/submit`, `/mod/astro`, `/methods`).  
3) Feed card UI.  
4) Post detail UI (safe embeds + images).  
5) Submit flow with validations + preview.  
6) AstroShield v1 (signals, scoring, chip, slowmode).  
7) Moderation tools.  
8) Safety hardening (CSP, consent, rate limits).  
9) Deploy V2 (staging → prod) with smoke tests.

## 13) Change Control
No scope changes without editing this file in the same PR. Any deviation is a defect.

