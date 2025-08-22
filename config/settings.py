# config/settings.py — GMFU (Good, Minimal, Fast, Understandable)
import os
from pathlib import Path

import dj_database_url  # make sure this is in requirements.txt

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Core
# -----------------------------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-dev-secret")
DEBUG = os.environ.get("DEBUG", "0").lower() in ("1", "true", "yes")

LANGUAGE_CODE = "en-au"
TIME_ZONE = "Australia/Brisbane"
USE_I18N = True
USE_TZ = True

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Your app(s)
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serve static from image
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# -----------------------------------------------------------------------------
# Database (Postgres via DATABASE_URL; safe local fallback only in DEBUG)
# -----------------------------------------------------------------------------
db_url = os.environ.get("DATABASE_URL", "").strip()

# Optional PG* var support (if you ever set PGHOST/PGUSER/etc.)
if not db_url:
    pg_host = os.environ.get("PGHOST")
    pg_port = os.environ.get("PGPORT", "5432")
    pg_user = os.environ.get("PGUSER")
    pg_pass = os.environ.get("PGPASSWORD")
    pg_db   = os.environ.get("PGDATABASE")
    if all([pg_host, pg_user, pg_pass, pg_db]):
        db_url = f"postgres://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

if not DEBUG and not db_url:
    raise RuntimeError("DATABASE_URL must be set in production")

if db_url:
    DATABASES = {
        "default": dj_database_url.parse(
            db_url,
            conn_max_age=int(os.environ.get("DB_CONN_MAX_AGE", "600")),
            ssl_require=False,  # Fly Postgres on private network; sslmode=disable is fine
        )
    }
else:
    # Local dev fallback
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Optional connection options
DATABASES["default"].setdefault("OPTIONS", {})
DATABASES["default"]["OPTIONS"].setdefault("connect_timeout", 30)

# -----------------------------------------------------------------------------
# Static / Media
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]  # keep if you have app-level assets

# WhiteNoise with hashed filenames; fail at build if missing
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

# Media (unchanged)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Optional: S3/Tigris for MEDIA uploads (toggle with DJANGO_USE_S3_MEDIA=1)
USE_S3_MEDIA = os.environ.get("DJANGO_USE_S3_MEDIA", "").lower() in ("1", "true", "yes")
if USE_S3_MEDIA:
    INSTALLED_APPS.append("storages")
    AWS_STORAGE_BUCKET_NAME = os.environ["BUCKET_NAME"]
    AWS_S3_ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL_S3")  # e.g. https://fly.storage.tigris.dev
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_ADDRESSING_STYLE = "virtual"
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_DEFAULT_ACL = "public-read"
    STORAGES["default"] = {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"}
else:
    STORAGES["default"] = {"BACKEND": "django.core.files.storage.FileSystemStorage"}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------------------------------------------------------------------
# Hosts / CSRF (Fly + Render) with env overrides
# -----------------------------------------------------------------------------
FLY_APP_NAME = os.environ.get("FLY_APP_NAME", "surejan")

DEFAULT_HOSTS = [
    "localhost",
    "127.0.0.1",
    "surejan.onrender.com",
    "surejan.fly.dev",
    f"{FLY_APP_NAME}.fly.dev",
    ".fly.dev",
]
_env_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "").strip()
if _env_hosts:
    ALLOWED_HOSTS = ["*"] if _env_hosts == "*" else [h.strip() for h in _env_hosts.split(",") if h.strip()]
else:
    ALLOWED_HOSTS = DEFAULT_HOSTS

CSRF_TRUSTED_ORIGINS = [
    "https://surejan.onrender.com",
    "https://surejan.fly.dev",
    f"https://{FLY_APP_NAME}.fly.dev",
]
_extra_csrf = os.environ.get("DJANGO_CSRF_TRUSTED", "").strip()
if _extra_csrf:
    CSRF_TRUSTED_ORIGINS += [o.strip() for o in _extra_csrf.split(",") if o.strip()]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

# -----------------------------------------------------------------------------
# Auth redirects
# -----------------------------------------------------------------------------
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
