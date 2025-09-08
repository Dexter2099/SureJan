#!/usr/bin/env bash
# Simple Fly.io deploy using existing Dockerfile and fly.toml
set -euo pipefail

# Ensure we're in the project root
[ -f manage.py ] || { echo "manage.py not found in CWD. cd into project root and re-run."; exit 1; }

# Resolve app name from FLY_APP or fly.toml (fallback: surejan)
APP="${FLY_APP:-}"
if [ -z "${APP}" ] && [ -f fly.toml ]; then
  APP="$(awk -F'\"' '/^app[[:space:]]*=/{print $2; exit}' fly.toml || true)"
fi
APP="${APP:-surejan}"
echo "Using Fly app name: ${APP}"

# Ensure Fly app exists and set as default for subsequent commands
fly apps create "${APP}" >/dev/null 2>&1 || true
export FLY_APP="${APP}"

# Optionally seed DJANGO_SECRET_KEY for new apps
if ! fly secrets list 2>/dev/null | awk '{print $1}' | grep -q '^DJANGO_SECRET_KEY$'; then
  if command -v python >/dev/null 2>&1; then
    SK="$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(64))
PY
)"
  else
    SK="$(openssl rand -base64 64 | tr -d '\n')"
  fi
  fly secrets set DJANGO_SECRET_KEY="$SK" >/dev/null
  echo "Set DJANGO_SECRET_KEY."
fi

# Deploy using the committed Dockerfile
fly deploy --remote-only --dockerfile Dockerfile "$@"

# Run database migrations
fly ssh console -C "python manage.py migrate --noinput" || \
  echo "WARNING: migrate failed via SSH; check logs."

# Basic status and reachability
fly status
fly logs --since 15m || true
curl -I "https://${APP}.fly.dev/" || true
