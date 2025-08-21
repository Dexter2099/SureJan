#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# 1. Clean up leftover Fly manifests
rm -f /tmp/manifest.json /tmp/session.json "$HOME/.fly/state.yml"

# 2. Ensure fly.toml has proper build and http_service sections
TOML="fly.toml"

# Ensure [build] dockerfile = "Dockerfile"
if grep -q '^\[build\]' "$TOML"; then
  sed -i '/^\[build\]/,/^\[/{/dockerfile/d}' "$TOML"
  sed -i '/^\[build\]/a\  dockerfile = "Dockerfile"' "$TOML"
else
  printf '\n[build]\n  dockerfile = "Dockerfile"\n' >> "$TOML"
fi

# Ensure [http_service] internal_port = 8000
if grep -q '^\[http_service\]' "$TOML"; then
  sed -i '/^\[http_service\]/,/^\[/{/internal_port/d}' "$TOML"
  sed -i '/^\[http_service\]/a\  internal_port = 8000' "$TOML"
else
  printf '\n[http_service]\n  internal_port = 8000\n' >> "$TOML"
fi

# 3. Verify Dockerfile ends with gunicorn CMD bound to 0.0.0.0:8000
if ! tail -n1 Dockerfile | grep -Eq 'CMD\s*\["gunicorn".*"--bind","0.0.0.0:8000"'; then
  echo "Dockerfile must end with gunicorn CMD binding to 0.0.0.0:8000"
  exit 1
fi

# 4. Ensure Django settings allow Fly domain, trusted origins, and static root
SETTINGS="config/settings.py"

# ALLOWED_HOSTS
if grep -q '^ALLOWED_HOSTS' "$SETTINGS"; then
  sed -i 's/^ALLOWED_HOSTS = .*/ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".fly.dev"]/' "$SETTINGS"
else
  sed -i '1iALLOWED_HOSTS = ["localhost", "127.0.0.1", ".fly.dev"]' "$SETTINGS"
fi

# CSRF_TRUSTED_ORIGINS
if grep -q '^CSRF_TRUSTED_ORIGINS' "$SETTINGS"; then
  sed -i 's|^CSRF_TRUSTED_ORIGINS = .*|CSRF_TRUSTED_ORIGINS = ["https://*.fly.dev"]|' "$SETTINGS"
else
  sed -i '/ALLOWED_HOSTS/aCSRF_TRUSTED_ORIGINS = ["https://*.fly.dev"]' "$SETTINGS"
fi

# STATIC_ROOT
if grep -q '^STATIC_ROOT' "$SETTINGS"; then
  sed -i 's|^STATIC_ROOT = .*|STATIC_ROOT = BASE_DIR / "staticfiles"|' "$SETTINGS"
else
  sed -i '/STATICFILES_DIRS/aSTATIC_ROOT = BASE_DIR / "staticfiles"' "$SETTINGS"
fi

# 5. Create Fly app named "surejan" if it doesn't exist
if ! fly apps show surejan >/dev/null 2>&1; then
  fly apps create surejan
fi

# 6. Deploy using remote builder
fly deploy --remote-only --dockerfile Dockerfile

# 7. Print status, recent logs, and perform a curl check
fly status
fly logs --tail 50
curl -I https://surejan.fly.dev/
