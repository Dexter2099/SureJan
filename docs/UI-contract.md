*** /dev/null
--- a/docs/UI-contract.md
@@
+# SureJan V2 — UI Contract (Authoritative Layout)
+> This file locks the layout for V2. If the UI changes, this file must change in the same PR.
+
+## Pages covered
+- **Home** `/` and **Community** `/r/<slug>` (same layout)
+- **Submit Post** `/submit`
+- (Reference only) Post detail `/p/<id>` uses the same grid as Home.
+
+## Grid & breakpoints
+- Max page width **1200px**, centered.
+- Columns: `[margin] | **Feed 700px** | 24px gutter | **Sidebar 300px** | [margin]`.
+- Mobile `<768px`: single column (Feed first), then Sidebar items stacked.
+
+## Header
+- Left: Logo → `/`
+- Center: Tabs **Hot · New · Top**
+- Right: `Login | Sign up` (or account menu). On mobile, show **Submit Post** as a header button.
+
+## Sidebar (right gutter)
+- **Submit Post** (primary CTA)
+- **Anti-Astroturf** link → `/methods`
+> No other widgets in V2.
+
+## Post card anatomy (Home/Community)
+- Meta: `r/<slug> • author • age`
+- Title (clamped 2 lines)
+- Optional media thumb (link or first image)
+- Actions: vote, comment count, **Astro chip**
+
+## Submit Post (wireframe fields)
+- Type: **Text** | **Link** | **Images (≤5 URLs)**
+- Fields: Title (required), Body (optional), Link URL (if Link), Up to 5 image URLs (if Images)
+- Preview toggle (optional)
+
+## Wireframes (ASCII, source of truth)
+### Home / Community
+```
+[LOGO]   Hot | New | Top                                   [Login/Account]
+┌─────────────────────────────────────────────────────────────────────────┐
+│           [ FEED ~700px ]       |      [ SIDEBAR 300px ]               │
+│  ┌───────────────────────────┐  |  ┌───────────────────────────────┐   │
+│  │ r/news • alice • 2h       │  |  │  [Submit Post] (primary)      │   │
+│  │ Big post title…           │  |  │  Anti-Astroturf → /methods    │   │
+│  │ [thumb]  ▲ 123  💬 45 [A] │  |  └───────────────────────────────┘   │
+│  └───────────────────────────┘  |                                       │
+│  (repeat cards…)                |                                       │
+└─────────────────────────────────────────────────────────────────────────┘
+```
+### Submit Post
+```
+[LOGO]   Hot | New | Top                                   [Login/Account]
+┌──────────────────────────────────────────────────────────┐
+│  Type: [Text|Link|Images]                                │
+│  Title: [______________________________]                 │
+│  Body:  [__________________________________________]     │
+│  Link URL (if Link): [___________________________]       │
+│  Image URLs (1–5):   [ ] [ ] [ ] [ ] [ ]                 │
+│  [Submit]                                     │
+└──────────────────────────────────────────────────────────┘
+```
+
+## Test selectors (must exist)
+- Feed: each post card root has `data-testid="post-card"`
+- Sidebar CTA: `data-testid="sidebar-submit"`
+- Anti-Astro link: `data-testid="sidebar-astro"`
+- Submit form: `data-testid="submit-form"`
+
+## Change control
+- If grid widths, header items, sidebar contents, or required selectors change, update this file in the same PR.
 