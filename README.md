# SureJan

SureJan is an independent, local-first forum inspired by old Reddit — built with **Django + HTMX + Postgres**, deployed on **Fly.io**.  
It’s designed to give real communities a place to speak freely, without interference from algorithms, astroturfing, or corporate manipulation.

**Status:** Live at [https://surejan.app/mission](https://surejan.app/mission)

---

## 🌱 Mission: Real Voices, Not Manufactured Consensus

SureJan was created to fight **astroturfing** — the practice of disguising coordinated influence operations as “grassroots” opinion.  
Our goal is to restore authenticity to online discussion by building transparent guardrails around how influence spreads.

We believe in:

- **Local-first design** – built for Brisbane, open for all.  
- **Transparency and fairness** – visible moderation and public rules.  
- **Privacy by default** – no tracking, no algorithmic feeds.  
- **Authenticity over astroturf** – protection against coordinated manipulation.  
- **Simplicity and speed** – old-school forums that load instantly and last.

---

## 🛡️ Anti-Astroturfing Engine

SureJan includes a built-in defence layer that detects and slows coordinated manipulation:

- Votes are bucketed into **30-second intervals** and analysed over **300-second windows**.
- **New account votes** are weighted differently to reduce sockpuppet power.
- A **threshold-based slowmode** activates when risk scores rise.
- Only **aggregate patterns** are stored — never personal data.

These systems aim to make human conversation resilient against synthetic consensus.

---

## ⚙️ Run Locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver

### Environment variables

- `DJANGO_SECRET_KEY` – random string, required
- `DATABASE_URL`
- `MEDIA_URL`
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`
- `SENTRY_DSN` – optional

Production secrets are set via `fly secrets` and should never be committed to the repo.

## Docs

- [Architecture](docs/architecture.md)
- [Smoke Tests](docs/runbooks/smoke.md)

## License

This project is licensed under the [MIT License](LICENSE).
