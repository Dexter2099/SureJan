# SureJan v3.1 — System Overview

**Goal:** Local-first community forum with anti-astroturf scoring.

```mermaid
flowchart LR
  A[Client] --> B[Cloudflare (surejan.app)]
  B --> C[Django app (Fly.io)]
  C <--> D[(Postgres)]
  C <--> E[(Tigris S3 - MEDIA)]
  C --> F[Static via Whitenoise]
  C --> G[/healthz]
```


Components

Edge: Cloudflare proxy; only surejan.app served.

App: Django (core now; target split posts/comments/votes/communities).

DB: Fly Postgres. Media: Tigris via MEDIA_URL. Static: Whitenoise.

Obs: Fly logs + /healthz; HTML error templates.


