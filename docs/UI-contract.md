Change control: If the UI changes, update this file in the same PR.

# SureJan V2 — UI Contract (Authoritative Layout)

## Pages covered
Home `/` · Community `/r/<slug>` · Submit `/submit` · (Detail `/p/<id>` uses same grid)

## Grid & breakpoints
Max width **1200px**; centered. Columns: `[margin] | **Feed ~700px** | 24px | **Sidebar 300–320px** | [margin]`.  
Mobile `<768px`: single column (Feed then Sidebar items stacked).

## Header
Left: **Logo + “Communities ▾”** (menu or link to `/r`).  
Center: **Hot · New · Top** (tabs).  
Right: `Login | Sign up` (or account). Mobile: **Submit Post** in header.

## Sidebar (desktop)
**Submit Post** (primary CTA)  
**Anti-Astroturf** → `/methods`  
> Nothing else in V2.

## Post card anatomy
Meta: `r/<slug> • author • age`  
Title (clamped 2 lines)  
Optional media thumb (link or first image)  
Actions: vote, comment count, **Astro chip**

## Submit Post (wireframe fields)
Type: **Text | Link | Images (≤5 uploads, ≤4MB each)**  
Fields: Title (required), Body (optional), Link URL (if Link), up to 5 images.  
**Submit** button (no preview required in V2).

## Theme & tokens
**Light theme default**. Use design tokens (see `Design-Tokens.md`). Ensure AA contrast.

## Required selectors (test hooks)
- Header: `data-testid="header-bar"`
- Sort tabs root: `id="sort-tabs"`
- Feed card root: `class="post-card"` + `data-testid="post-card"`
- Sidebar CTA: `data-testid="sidebar-submit"`
- Anti-Astro link: `data-testid="sidebar-astro"`
- Submit form: `data-testid="submit-form"`

