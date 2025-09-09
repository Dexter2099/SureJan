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
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# -----------------------------------------------------------------------------
# Security / Debug
# -----------------------------------------------------------------------------
DEBUG = os.environ.get("DJANGO_DEBUG", "1") in ("1", "true", "True")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or os.environ.get("SECRET_KEY")
if not DEBUG:
    if not SECRET_KEY or SECRET_KEY == "dev-secret-key":
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY or SECRET_KEY must be set in production"
        )
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
    "surejan.app",
    "www.surejan.app",
]

_env_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "").strip()
if _env_hosts:
    ALLOWED_HOSTS = ["*"] if _env_hosts == "*" else [h.strip() for h in _env_hosts.split(",") if h.strip()]
else:
    ALLOWED_HOSTS = DEFAULT_HOSTS

ALLOWED_HOSTS = list(
    sorted(
        set(ALLOWED_HOSTS)
        | {"surejan.app", "www.surejan.app"}
    )
)

CSRF_TRUSTED_ORIGINS = [
    "https://surejan.onrender.com",
    "https://surejan.fly.dev",
    f"https://{FLY_APP_NAME}.fly.dev",
    "https://surejan.app",
    "https://www.surejan.app",
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

# Removed legacy thumbnail and provider-specific settings

# Simple per-user rate limits
RATE_POSTS_PER_DAY_NEW = int(os.getenv("RATE_POSTS_PER_DAY_NEW", "10"))
RATE_COMMENTS_PER_MIN_NEW = int(os.getenv("RATE_COMMENTS_PER_MIN_NEW", "8"))
RATE_VOTES_PER_MIN_NEW = int(os.getenv("RATE_VOTES_PER_MIN_NEW", "40"))

RATE_POSTS_PER_DAY_AUTH = int(os.getenv("RATE_POSTS_PER_DAY_AUTH", "30"))
RATE_COMMENTS_PER_MIN_AUTH = int(os.getenv("RATE_COMMENTS_PER_MIN_AUTH", "20"))
RATE_VOTES_PER_MIN_AUTH = int(os.getenv("RATE_VOTES_PER_MIN_AUTH", "120"))

RATE_LIMITS = {
    "post": {"limit": RATE_POSTS_PER_DAY_AUTH, "window": 86400},  # posts per day
    "comment": {"limit": RATE_COMMENTS_PER_MIN_AUTH, "window": 60},  # comments per minute
    "vote": {"limit": RATE_VOTES_PER_MIN_AUTH, "window": 60},  # votes per minute
}

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    # Exempt Fly’s HTTP health probe hitting internal :8000
    SECURE_REDIRECT_EXEMPT = [r"^healthz$"]
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    MEDIA_STORAGE_HOST = os.getenv(
        "MEDIA_STORAGE_HOST", "https://surejan-media.fly.storage.tigris.dev"
    )

    CONTENT_SECURITY_POLICY = {
        "DIRECTIVES": {
            "default-src": ("'self'",),
            "script-src": ("'self'",),
            "style-src": ("'self'", "'unsafe-inline'"),
            "img-src": ("'self'", "data:", MEDIA_STORAGE_HOST),
            "connect-src": ("'self'",),
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
    "storages",
    "communities",
    "core",
    "comments",
    "votes",
]
# explicitly lock the project to Django's built-in user
AUTH_USER_MODEL = "auth.User"

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
APPEND_SLASH = False

# -----------------------------------------------------------------------------
# Static / Media
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Detect build phase for collectstatic
IS_BUILD = os.getenv("DJANGO_COLLECTSTATIC") == "1"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STORAGES = {"staticfiles": {"BACKEND": STATICFILES_STORAGE}}

# Enforce manifest integrity for static files to surface missing references.
WHITENOISE_MANIFEST_STRICT = True

# Required envs
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL", "")  # e.g. https://fly.storage.tigris.dev
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "auto")

# Determine if S3 is fully configured and enabled
required = {
    "AWS_STORAGE_BUCKET_NAME": AWS_STORAGE_BUCKET_NAME,
    "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
    "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
    "AWS_S3_ENDPOINT_URL": AWS_S3_ENDPOINT_URL,
    "MEDIA_URL": os.getenv("MEDIA_URL", ""),
}

# Basic placeholder detection so sample values like "your-bucket" don't enable S3
placeholder_tokens = [
    "your-bucket",
    "your-access-key",
    "your-secret",
    "your-endpoint",
]
has_placeholders = any(
    token in (value or "")
    for value in required.values()
    for token in placeholder_tokens
)

USE_S3 = os.getenv("USE_S3", "1") in ("1", "true", "True")
if USE_S3 and all(required.values()) and not has_placeholders and not IS_BUILD:
    MEDIA_URL = required["MEDIA_URL"]
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_ADDRESSING_STYLE = "virtual"
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_DEFAULT_ACL = "public-read"
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "public, max-age=94608000"}
else:
    # Fallback to local storage so development and misconfigured deployments
    # serve media from /media/.
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    MEDIA_ROOT = BASE_DIR / "media"
    MEDIA_URL = "/media/"

# Ensure STORAGES['default'] points to the active storage backend
STORAGES["default"] = {"BACKEND": DEFAULT_FILE_STORAGE}

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
ASTROTURF_WATCH = os.environ.get("ASTROTURF_WATCH", "1") in (
    "1",
    "true",
    "True",
)
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
