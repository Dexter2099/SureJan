# config/settings.py — GMFU (Good, Minimal, Fast, Understandable)
import os
from pathlib import Path

import dj_database_url  # make sure this is in requirements.txt

BASE_DIR = Path(__file__).resolve().parent.parent

IS_COLLECTSTATIC = os.getenv("DJANGO_COLLECTSTATIC") == "1"
DEBUG = os.getenv("DEBUG", "0").lower() in ("1", "true", "yes")

# -----------------------------------------------------------------------------
# Core
# -----------------------------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-dev-secret")

LANGUAGE_CODE = "en-au"
TIME_ZONE = "Australia/Brisbane"
USE_I18N = True
USE_TZ = True

# Keep DB connections open briefly to reduce churn
CONN_MAX_AGE = int(os.environ.get("DB_CONN_MAX_AGE", "60"))

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
db_url = os.getenv("DATABASE_URL", "").strip()

# Optional PG* var support (if you ever set PGHOST/PGUSER/etc.)
if not db_url:
    pg_host = os.getenv("PGHOST")
    pg_port = os.getenv("PGPORT", "5432")
    pg_user = os.getenv("PGUSER")
    pg_pass = os.getenv("PGPASSWORD")
    pg_db   = os.getenv("PGDATABASE")
    if all([pg_host, pg_user, pg_pass, pg_db]):
        db_url = f"postgres://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

if not DEBUG and not IS_COLLECTSTATIC and not db_url:
    raise RuntimeError("DATABASE_URL must be set in production")

if db_url:
    DATABASES = {
        "default": dj_database_url.parse(
            db_url,
            conn_max_age=CONN_MAX_AGE,
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
if DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
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

if DEBUG:
    STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.StaticFilesStorage"

if DEBUG:
    STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.StaticFilesStorage"

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
# Hosts / CSRF
# -----------------------------------------------------------------------------
ALLOWED_HOSTS = [h for h in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if h]

# Keep CSRF tight even if ALLOWED_HOSTS is broad
CSRF_TRUSTED_ORIGINS = [
    "https://surejan.fly.dev",
    "https://www.surejan.com",
]

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
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
