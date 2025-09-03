# SureJan V3 — Wireframes

This folder contains the exported **Penpot wireframes** for SureJan V3.

## Pages covered
- **Main Page** (`V3-Main-Page.svg/png`)
  - Header 128px tall (Logo → Home, Tabs Hot/New/Top, Account/Login)
  - Left sidebar: Communities list (News, Brisbane, Politics, Social)
  - Center: Feed 700px
  - Gutter 24px
  - Right sidebar: Account/Login, Submit Post CTA, Anti-Astroturf link
- **Submit Post Page** (`V3-Submit-Post.svg/png`)
  - Community selector (required)
  - Post Title (required)
  - Optional media (image/link/video)
  - Optional body text
  - Submit button
- **Post Detail Page** (`V3-Post-Detail.svg/png`)
  - Full post (title, meta, media, body, actions)
  - Comment input + comment thread
  - Same left/right sidebars as other pages

## Usage
- These wireframes are **layout references only**.  
- All code must follow the authoritative spec in `docs/V3-onepager.md` and `docs/UI-contract.md`.  
- If wireframes or layout change, update this folder and the spec files in the **same PR**.

## Export formats
- `.svg` → scalable vector reference for dev/design
- `.png` → quick preview for GitHub
- `.pdf` → optional combined export for sharing

---

**Change control:**  
Any change to the UI layout (header, grid widths, sidebar contents, form fields) must update:
1. `docs/V3-onepager.md`
2. `docs/UI-contract.md`
3. The exports in this folder
