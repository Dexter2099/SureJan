# config/settings.py — GMFU (Good, Minimal, Fast, Understandable)
from pathlib import Path
import os
import dj_database_url
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from django.core.exceptions import ImproperlyConfigured

# -----------------------------------------------------------------------------
# Base
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Security / Debug
# -----------------------------------------------------------------------------
DEBUG = os.environ.get("DJANGO_DEBUG", "1") in ("1", "true", "True")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not DEBUG:
    if not SECRET_KEY or SECRET_KEY == "dev-secret-key":
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set in production")
else:
    SECRET_KEY = SECRET_KEY or "dev-secret-key"

if dsn := os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
    )

# -----------------------------------------------------------------------------
# Hosts / CSRF (Fly + optional Render) with env overrides
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

# --- Dev proxy defaults (only in DEBUG) ---
if DEBUG:
    _dev_allowed = {"localhost", "127.0.0.1", "surejan.internal", "surejan.fly.dev"}
    ALLOWED_HOSTS = list(sorted(set(ALLOWED_HOSTS) | _dev_allowed))
    # allow HTTP localhost origins for forms while using the proxy
    _dev_csrf = {
        "http://localhost:8080", "http://127.0.0.1:8080",
        "http://localhost:8888", "http://127.0.0.1:8888",
    }
    CSRF_TRUSTED_ORIGINS = list(sorted(set(CSRF_TRUSTED_ORIGINS + list(_dev_csrf))))

# Respect Fly proxy for secure detection
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_SECURE = not DEBUG

ENABLE_TWITTER_EMBEDS = os.environ.get("ENABLE_TWITTER_EMBEDS", "0") in (
    "1",
    "true",
    "True",
)

EMBED_WHITELIST = [
    "https://www.youtube.com",
    "https://www.youtube-nocookie.com",
    "https://rumble.com",
]
if ENABLE_TWITTER_EMBEDS:
    EMBED_WHITELIST.append("https://platform.twitter.com")

# Simple per-user rate limits
RATE_LIMITS = {
    "post": {"limit": 20, "window": 86400},  # posts per day
    "comment": {"limit": 60, "window": 60},  # comments per minute
    "vote": {"limit": 120, "window": 60},  # votes per minute
}

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    # Exempt Fly’s HTTP health probe hitting internal :8000
    SECURE_REDIRECT_EXEMPT = [r"^healthz$"]
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    CONTENT_SECURITY_POLICY = {
        "DIRECTIVES": {
            "default-src": ("'self'",),
            "script-src": ("'self'",),
            "style-src": ("'self'", "'unsafe-inline'"),
            "img-src": ("'self'", "https:", "data:"),
            "connect-src": ("'self'",),
            "frame-src": tuple(["'self'"] + EMBED_WHITELIST),
            "frame-ancestors": ("'self'",),
            "upgrade-insecure-requests": True,
            "base-uri": ("'self'",),
            "form-action": ("'self'",),
            "object-src": ("'none'",),
        }
    }

# -----------------------------------------------------------------------------
# Admin
# -----------------------------------------------------------------------------
ADMIN_URL = os.environ.get("DJANGO_ADMIN_URL", "secret-admin/").strip("/") + "/"
ADMIN_IP_ALLOWLIST = {
    ip.strip()
    for ip in os.environ.get("ADMIN_IP_ALLOWLIST", "").split(",")
    if ip.strip()
}

# -----------------------------------------------------------------------------
# Apps / Middleware
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "csp",   # django-csp
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.AdminIPAllowlistMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "core.middleware.ActionRateLimitMiddleware",
    "csp.middleware.CSPMiddleware",  # django-csp v4
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context.astro_constants",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# -----------------------------------------------------------------------------
# Database (DATABASE_URL with SQLite fallback; keep-alive)
# -----------------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", "sqlite:///db.sqlite3"),
        conn_max_age=60,
        ssl_require=False,
    )
}

# -----------------------------------------------------------------------------
# Password validation
# -----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    }
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

# -----------------------------------------------------------------------------
# I18N
# -----------------------------------------------------------------------------
LANGUAGE_CODE = "en-au"
TIME_ZONE = "Australia/Brisbane"
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# Static / Media
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

if os.getenv("DJANGO_TESTS", "1") in ("1", "true", "True"):
    STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    }
else:
    STORAGES = {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        }
    }

STATICFILES_STORAGE = STORAGES["staticfiles"]["BACKEND"]

# Temporary guard to avoid 500s from missing manifest entries while iterating.
# REMOVE once favicon/static references are correct and collectstatic is clean.
WHITENOISE_MANIFEST_STRICT = False

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
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "public, max-age=94608000"}
    STORAGES["default"] = {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"}
else:
    STORAGES["default"] = {"BACKEND": "django.core.files.storage.FileSystemStorage"}

# -----------------------------------------------------------------------------
# Email
# -----------------------------------------------------------------------------
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("EMAIL_HOST", "")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "25"))
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "0") in ("1", "true", "True")
    EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "0") in ("1", "true", "True")

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@surejan.fly.dev")

# -----------------------------------------------------------------------------
# Misc
# -----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Public auth redirects
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# -----------------------------------------------------------------------------
# Astroturf detection constants
# -----------------------------------------------------------------------------
ASTROTURF_WATCH = True
ASTRO_WINDOW_S = 300
ASTRO_BUCKET_S = 30
ASTRO_BASELINE_LOOKBACK_D = 30
ASTRO_NEW_ACCOUNT_DAYS = 7
ASTRO_EARLY_VOTES_N = 50
ASTRO_MIN_EARLY_VOTES = 20
ASTRO_EARLY_SHARE_RED = 0.60
ASTRO_BAND_AMBER = 40
ASTRO_BAND_RED = 70
ASTRO_SLOWMODE_THRESHOLD = 70
ASTRO_SLOWMODE_RATE = "1/5m"

# Logging (simple console)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
