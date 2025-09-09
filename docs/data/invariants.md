# Data Invariants

- Post slugs unique per community.
- One active vote per (user,target).
- Image uploads: JPEG/PNG only; size ≤ N MB; under `MEDIA_URL`.
- AstroShield score ∈ [1,100]; bands: 0–39 Normal, 40–69 Watch, 70–84 High, 85+ Severe.
- Astro chips color palette is fixed (not affected by global theme changes).

