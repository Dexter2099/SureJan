# config/settings.py
import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Core
# -----------------------------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-dev-secret")
DEBUG = os.environ.get("DEBUG", "0") in ("1", "true", "True")

LANGUAGE_CODE = "en-au"
TIME_ZONE = "Australia/Brisbane"
USE_I18N = True
USE_TZ = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serve static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
db_url = os.environ.get("DATABASE_URL", "").strip()

# Support Fly Managed Postgres (PG* vars) if DATABASE_URL isn’t provided
pg_host = os.environ.get("PGHOST")
pg_port = os.environ.get("PGPORT", "5432")
pg_user = os.environ.get("PGUSER")
pg_pass = os.environ.get("PGPASSWORD")
pg_db   = os.environ.get("PGDATABASE")

if not db_url and all([pg_host, pg_user, pg_pass, pg_db]):
    db_url = f"postgres://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

if db_url:
    DATABASES = {
        "default": dj_database_url.parse(db_url, conn_max_age=600, ssl_require=False)
    }
else:
    # Fallback to SQLite so the app boots even if DB is missing
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# -----------------------------------------------------------------------------
# Static / Media
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------------------------------------------------------------------
# Hosts / CSRF (Render + Fly)
# -----------------------------------------------------------------------------
FLY_APP_NAME = os.environ.get("FLY_APP_NAME", "surejan")

ALLOWED_HOSTS = [
    "localhost", "127.0.0.1",
    "surejan.onrender.com",
    "surejan.fly.dev",
    f"{FLY_APP_NAME}.fly.dev",
    ".fly.dev",
]

CSRF_TRUSTED_ORIGINS = [
    "https://surejan.onrender.com",
    "https://surejan.fly.dev",
    f"https://{FLY_APP_NAME}.fly.dev",
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
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
