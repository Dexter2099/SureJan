# ---------- Base ----------
FROM python:3.12-slim
ARG BUILD_REV=dev
ENV BUILD_REV=${BUILD_REV}

# Prevent .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ---------- App setup ----------
WORKDIR /app

# Install Python deps first (better cache)
COPY requirements.txt .
RUN pip install --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static at build (no favicon checks)
RUN DJANGO_COLLECTSTATIC=1 python manage.py collectstatic --noinput --clear

# Optional: drop privs
RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# ---------- Runtime ----------
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--threads", "2", \
     "--timeout", "90", \
     "--graceful-timeout", "30", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
