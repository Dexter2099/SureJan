# ---------- Base ----------
FROM python:3.12-slim
ARG BUILD_REV=dev
ENV BUILD_REV=${BUILD_REV}

# Prevent .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:$PATH"

# System deps (keep lean)
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      curl \
    && rm -rf /var/lib/apt/lists/*

# ---------- App setup ----------
WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy the project
COPY . .

# After installing deps and copying source
RUN python manage.py collectstatic --noinput --clear

# Fail the build if static pipeline would break
RUN python - <<'PY'
import os
from django.conf import settings
from django import setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
setup()
from django.templatetags.static import static
assert static("favicon.ico"), "favicon.ico not found in collected static"
PY

# Optional: run as a non-root user for safety
RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# ---------- Runtime ----------
# Fly’s internal port is set in fly.toml (internal_port = 8000)
EXPOSE 8000

# Keep Gunicorn modest for a 512 MB machine
# - 2 workers + 2 threads gives decent concurrency without OOM
# - timeouts avoid hung startups blocking health checks
# - log to stdout/stderr so `flyctl logs` shows issues
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--threads", "2", \
     "--timeout", "60", \
     "--graceful-timeout", "30", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
