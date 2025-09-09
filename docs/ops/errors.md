# Error Handling & Health

- Error templates: `templates/errors/{400,403,404,413,429,500}.html`
- Handlers wired in `config/urls.py` (keep them).
- Health endpoint `/healthz` → 200 when app + DB reachable.

