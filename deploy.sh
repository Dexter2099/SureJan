#!/usr/bin/env bash
# One-shot Fly.io deploy for your Django app using a Dockerfile (no Launch/buildpacks/mise)
# - Creates/patches Dockerfile, .dockerignore, fly.toml
# - Patches Django settings for Fly
# - Ensures app exists, deploys with remote builder, runs migrations
# - Shows status/logs and does a reachability check
set -euo pipefail

echo "==> 0) Sanity: repo root?"
[ -f manage.py ] || { echo "manage.py not found in CWD. cd into your Django project root and re-run."; exit 1; }

# Resolve app name (from existing fly.toml, env FLY_APP, or default)
APP="${FLY_APP:-}"
if [ -z "${APP}" ] && [ -f fly.toml ]; then
  APP="$(awk -F'\"' '/^app[[:space:]]*=/{print $2; exit}' fly.toml || true)"
fi
APP="${APP:-surejan}"
echo "Using Fly app name: ${APP}"

echo "==> 1) Nuke Launch/session leftovers (avoid Launch path entirely)"
rm -f /tmp/manifest.json /tmp/session.json ~/.fly/state.yml || true

echo "==> 2) Write Dockerfile (gunicorn on 0.0.0.0:8000)"
cat > Dockerfile <<'EOF'
# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Collect static (ignore if not configured yet)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000
CMD ["gunicorn","config.wsgi:application","--bind","0.0.0.0:8000","--workers","3","--timeout","90"]
EOF

echo "==> 3) .dockerignore"
cat > .dockerignore <<'EOF'
.git
__pycache__/
*.pyc
*.pyo
*.pyd
.env
venv/
.venv/
node_modules/
media/
staticfiles/
dist/
build/
.DS_Store
# keep buildpacks out of context just in case
.tool-versions
.mise.toml
EOF

echo "==> 4) fly.toml: force Dockerfile build + correct port + health check"
if [ ! -f fly.toml ]; then
  cat > fly.toml <<EOF
app = "${APP}"
primary_region = "syd"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 1
  processes = ["app"]

  [[http_service.checks]]
    grace_period = "10s"
    interval = "30s"
    timeout = "5s"
    method = "GET"
    path = "/"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
EOF
else
  # Ensure [build].dockerfile and internal_port=8000 present/updated
  awk '
    BEGIN{have_build=0; have_df=0}
    /^\[build\]/{have_build=1}
    have_build && /dockerfile *=/{have_df=1}
    {print}
    END{
      if(!have_build){print "\n[build]"; print "  dockerfile = \"Dockerfile\""}
      else if(!have_df){print "  dockerfile = \"Dockerfile\""}
    }' fly.toml | \
  awk '{sub(/internal_port *= *[0-9]+/,"internal_port = 8000")}1' > .fly.toml.tmp
  mv .fly.toml.tmp fly.toml
fi

echo "==> 5) Patch Django settings for Fly (ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, STATIC_ROOT)"
SETTINGS="config/settings.py"
if [ -f "$SETTINGS" ]; then
  grep -q '^ALLOWED_HOSTS' "$SETTINGS" \
    && sed -i 's/^ALLOWED_HOSTS.*/ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".fly.dev"]/' "$SETTINGS" \
    || printf '\nALLOWED_HOSTS = ["localhost", "127.0.0.1", ".fly.dev"]\n' >> "$SETTINGS"

  grep -q '^CSRF_TRUSTED_ORIGINS' "$SETTINGS" \
    && sed -i 's|^CSRF_TRUSTED_ORIGINS.*|CSRF_TRUSTED_ORIGINS = ["https://*.fly.dev"]|' "$SETTINGS" \
    || printf 'CSRF_TRUSTED_ORIGINS = ["https://*.fly.dev"]\n' >> "$SETTINGS"

  grep -q '^STATIC_ROOT' "$SETTINGS" || printf 'STATIC_ROOT = BASE_DIR / "staticfiles"\n' >> "$SETTINGS"
else
  echo "WARNING: ${SETTINGS} not found. If your settings live elsewhere, adjust the SETTINGS path."
fi

echo "==> 6) Ensure Fly app exists and is set as default"
fly apps create "${APP}" || true
# Make sure subsequent commands use this app implicitly
export FLY_APP="${APP}"

echo "==> 7) Secrets sanity (non-destructive). Set SECRET_KEY if missing; DATABASE_URL is up to you."
if ! fly secrets list 2>/dev/null | awk '{print $1}' | grep -q '^SECRET_KEY$'; then
  # Try to generate a random SECRET_KEY (python or openssl fallback)
  if command -v python >/dev/null 2>&1; then
    SK="$(python - <<'PY'
import secrets, string
print(secrets.token_urlsafe(64))
PY
)"
  else
    SK="$(openssl rand -base64 64 | tr -d '\n' )"
  fi
  fly secrets set SECRET_KEY="$SK" >/dev/null
  echo "Set SECRET_KEY."
else
  echo "SECRET_KEY already set."
fi
# Uncomment and set your DB if you want to enforce here:
# fly secrets set DATABASE_URL='postgres://user:pass@host:port/dbname'

echo "==> 8) Deploy using Dockerfile on remote builder (no Launch/buildpacks)"
fly deploy --remote-only --dockerfile Dockerfile

echo "==> 9) Run database migrations on the machine"
fly ssh console -C "python manage.py migrate --noinput" || {
  echo "WARNING: migrate failed via SSH; check logs. Continuing…"
}

echo "==> 10) Status, logs, reachability"
fly status
fly logs --since 15m || true
curl -I "https://${APP}.fly.dev/" || true

echo "==> Done. If unreachable, run:"
echo "   fly logs --since 10m"
echo "   fly ssh console -C 'ss -ltnp || netstat -ltnp'   # expect gunicorn on 0.0.0.0:8000"

