# Runbook — Smoke Tests

- `/healthz` → 200
- `/` → 200 (Hot/New visible)
- `/c/brisbane/` → 200
- `/p/<known-id>/` → 200; astro-chip visible
- Comment POST → 302/200
- Vote POST (+1 then 0) → counts correct and idempotent

