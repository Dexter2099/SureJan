Change control: If this spec changes, update this file in the same PR.

# SureJan V2 — One-Pager (Authoritative Spec)

## 1) Purpose
Ship a small, fast, safe **local forum** for **4 communities** with simple posting, comments, basic voting, and first-pass anti-astroturf (**AstroShield v1**). Target: **first 500 users**.

## 2) Scope
**In:** 4 communities (seeded) · Posts (Text/Link/Images ≤5) · Comments · Up/Down vote · Roles (Guest/User/Mod/Admin) · Mod actions (Remove/Lock/Slowmode/Domain-throttle) · AstroShield v1 · Strict CSP · Server-rendered pages · Fly.io + Postgres · Light theme.
**Out:** OAuth/Social login, rich editors, DMs/notifications, appeals, pins/manual boosts, full-text search, theming/i18n, analytics, mobile app.

## 3) URLs & Navigation
`/` Home feed · `/r/<slug>` Community feed · `/p/<id>` Post detail · `/submit` Submit · `/mod/astro` Mod list · `/methods` Safety & methods.
**Header:** Left **Logo + “Communities ▾”**; Center **Hot · New · Top**; Right Auth.  
**Community switching:** behind “Communities ▾” (no permanent header tabs).

## 4) UX & Layout (baseline)
Centered feed ≈**700px** + right sidebar **300–320px**. Mobile: single column.  
Sidebar (desktop): **Submit Post** (primary) + **Anti-Astroturf → /methods**.

## 5) Data & Rules (light sketch)
`Community(slug,name,…)` · `Post(author, community, title, body?, url?, images[≤5])` · `Comment(author,post,body)` · `Vote(user,{post|comment}, value∈{-1,+1})` · `AstroScore(object_id,score:int,band:str,signals:json)`.  
Flags: `is_deleted`, `is_removed`, `is_locked`, `slowmode_seconds(0)`, `domain_weight(0|-50)`.  
Visibility: `visible = not is_deleted and not is_removed`.

## 6) Post Types & Media
**Text** (markdown like Reddit) · **Link** (external) · **Images** (**≤5 uploads**, each **≤4MB**).
**Title ≤300 chars**; body markdown; sanitize output.

## 7) Sorting & Time Filter
Default `sort=hot`. Tabs: **Hot**, **New**, **Top**.  
**Top only** accepts `t ∈ {24h, 7d, all}`; if `sort=top` and `t` unset → **t=all**. No `t` elsewhere.

## 8) AstroShield v1
Score **1–100**. Bands: **0–39 green**, **40–69 amber**, **70–100 red**.  
Signals (cap at 100, last 24h unless stated):
- Account age <3 days → +25
- Vote velocity: >20/min (last hr) → +25; >40/min → +40 (use max)
- Posts/day >10 → +20
- Discuss ratio (comments:upvotes on user’s posts) <0.2 → +10
- Domain repetition >70% of user’s link posts to same domain → +10
Actions:
- Green: none.
- Amber (40–69): chip **“Watch”**.
- Red (≥70): chip **“High risk”**, **slowmode 60s**.
- Severe (≥85): **slowmode 120s**, list in `/mod/astro`.
Decay: recompute hourly; score drops as activity normalizes.
Chip styles (light theme):  
Green “Normal”; Amber “Watch” (text #92400e / bg #fef3c7); Red “High risk” (text #991b1b / bg #fee2e2).

## 9) Moderation
**Domain-throttle:** −50% ranking weight; set by **Mods/Admins**; auto-expires after **7 days**.  
**Remove = soft** (placeholder remains).  
**Author self-delete ≤15m:** no comments → hard-delete; else replace with **“[deleted]”**.  
Locked copy:
- “**Removed by moderators**.”
- “**[deleted]** by author.”
- “You can delete your post within **15 minutes** of publishing.”

## 10) Safety & Privacy
Strict **CSP allowlist**; **no third-party JS**. Rate limits (below).

## 11) Rate Limits (defaults; env-tunable)
**New users (<24h):** Posts **5/day**, Comments **6/min** (sliding), Votes **10/min**.  
**Authenticated (≥24h):** Posts **10/day**, Comments **1/min**, Votes **2/min**.  
Friendly 429 UI: “You’re going too fast. Please slow down and try again.”  
ENV (fallbacks above):  
`RATE_POSTS_PER_DAY_NEW=5` `RATE_COMMENTS_PER_MIN_NEW=6` `RATE_VOTES_PER_MIN_NEW=10`  
`RATE_POSTS_PER_DAY_AUTH=10` `RATE_COMMENTS_PER_MIN_AUTH=1` `RATE_VOTES_PER_MIN_AUTH=2`

## 12) Accessibility & UX
Contrast: **WCAG AA** (≥4.5:1 text, ≥3:1 large).  
Focus: visible 2px outline (accent color), never removed.  
Keyboard: tabs use L/R + Enter/Space, `aria-current`; “Communities ▾” uses `aria-haspopup="menu"`, `aria-expanded`, ESC closes; full keyboard nav.  
Locked strings:  
Feed empty “**No posts yet.**” · Community empty “**Nothing here yet.**” · Error “**Something went wrong.**” · Permission “**You need to sign in.**”

## 13) Ops & Environments
Staging: `surejan-staging.fly.dev` (**seed allowed**). Prod: `surejan.fly.dev` (**no seed**).  
ENV flags:  
`ALLOW_SEED=true|false` (staging true, prod false) · `CSP_REPORT_ONLY=true|false` (staging true) · `CSP_REPORT_URI=<url>` (optional) · `SENTRY_DSN` (prod required).  
Fly: `release_command: python manage.py migrate --noinput`. Static via WhiteNoise.

## 14) Definition of Done (V2)
- Hot/New/Top behave as above; Top defaults `t=all`.
- Submit supports Text/Link/Images(≤5 uploads) with validation.
- Detail shows images; clicking opens in a new tab; comments + votes work.
- AstroShield chips + slowmode thresholds work; `/methods` published.
- Mod tools (Remove/Lock/Slowmode/Domain-throttle) function.
- CSP enforced; consent gating; rate limits enforced.
- Staging + Prod live; acceptance checks are manual (no UI smoke tests); deps pinned.
- **500 registered users** milestone.

## 15) Acceptance
Acceptance checks are manual (no UI smoke tests). Targeted unit/integration tests only as needed.

## 16) Milestones (merge order)
1) Models/migrations + seed 4 communities · 2) Routes/base views · 3) Feed cards  
4) Post detail (images; opens in new tab) · 5) Submit + validation · 6) AstroShield v1
7) Moderation tools · 8) Safety hardening (CSP/consent/rates) · 9) Deploy V2 (staging→prod)

