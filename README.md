
---

# SureJan

SureJan is an independent, Brisbane-built community forum inspired by the old Reddit layout. It is designed to provide a fast and simple way for locals to post, comment, and vote without interference from algorithms, astroturfing, or excessive big-tech influence.

**Live site:** [https://surejan.app](https://surejan.app)

## Features (MVP)

* **Community Feeds**: Old-Reddit style feeds with sorting options (Best, Hot, New, Rising, Controversial, Top). Pagination set to 25 posts per page.
* **Seed Communities**: Two initial communities, `news` and `brisbane`, seeded via a management command.
* **User Accounts**: Username and password based authentication (email optional). Accounts display total “points” (sum of post and comment votes).
* **Posts**: Supports text or link submissions. Posts can be assigned to communities and rendered with basic Markdown formatting.
* **Comments**: Threaded comment trees with reply support, relative timestamps, and Markdown.
* **Voting**: Upvote and downvote support for posts and comments. Voting updates dynamically with HTMX requests. Rate limits apply to reduce spam.
* **Profiles**: Public user profiles with tabs for Overview, Posts, and Comments. Pagination provided for long histories.
* **Authentication & Security**: Secure session cookies, CSRF protection, CAPTCHA during signup, recovery codes for account resets, and basic rate limiting.

## Tech Stack

* **Backend**: Django 5, Python 3.12+
* **Frontend**: HTMX for partial page updates, Django templates for rendering
* **Database**: Postgres, SQLite fallback for development
* **Deployment**: Fly.io with Docker-based builds
* **Static Files**: WhiteNoise for static file serving, optional S3-compatible storage for media (Tigris, AWS S3)
* **Security**: django-csp, CSRF protection, secure session and cookie handling
* **Testing**: Django test framework with HTMX request coverage

## Development Setup

```bash
git clone https://github.com/Dexter2099/SureJan.git
cd SureJan
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_basics
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to access the dev server.

## Status

SureJan is an early-stage MVP. Contributions, bug reports, and feedback are welcome.
This project was developed and MVP shipped in three weeks with the use of AI coding agents.

---



<img width="673" height="718" alt="Surejan Public beta" src="https://github.com/user-attachments/assets/6086515d-cfd1-44b7-8591-b21057b975ff" />

