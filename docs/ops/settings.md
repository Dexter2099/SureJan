# Settings & Secrets

| ENV var              | Required | Used by | Example |
|----------------------|----------|--------|---------|
| DJANGO_SECRET_KEY    | Yes      | Django | random |
| DATABASE_URL         | Yes      | DB     | postgres://... |
| MEDIA_URL            | Yes      | Media  | https://surejan-media.fly.storage.tigris.dev/ |
| ALLOWED_HOSTS        | Yes      | Sec    | surejan.app,www.surejan.app,127.0.0.1 |
| CSRF_TRUSTED_ORIGINS | Yes      | Sec    | https://surejan.app,https://www.surejan.app |
| SUREJAN_READONLY     | No       | Views  | 1/0 |

Policy: block `.fly.dev` in both ALLOWED_HOSTS and CSRF; only serve `surejan.app`.

