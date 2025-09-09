# SureJan

SureJan is a lightweight, local-first forum inspired by old Reddit, built with Django + HTMX + Postgres, deployed on Fly.io. It relies on Django's built-in authentication system and default `auth.User` model.

Status: Down, uknown interfence from outsite source?

## Anti-astroturfing

SureJan includes a built‑in defence against coordinated manipulation:

- Early votes are analysed in 30‑second buckets and grouped over 300 seconds.
- Votes from new accounts are weighted differently to limit sockpuppet impact.
- A threshold-based flagging system slows posts when the risk score rises, placing them in slowmode for review.
- Only aggregate patterns are reviewed; personal data is never stored.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # Or create manually on Windows
python manage.py migrate
python manage.py runserver
```

### Environment variables

- `DJANGO_SECRET_KEY` – random string, required
- `DATABASE_URL`
- `MEDIA_URL`
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`
- `SENTRY_DSN` – optional

Production secrets are set via `fly secrets` and should never be committed to the repo.

## License

This project is licensed under the [MIT License](LICENSE).
