from .base import *

DEBUG = False

# Allow Fly health probe (Host: localhost) + your public domains only
ALLOWED_HOSTS = ["localhost", "surejan.app", "www.surejan.app"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Ensure CSRF trusts your Cloudflare-facing domains
CSRF_TRUSTED_ORIGINS = [
    "https://surejan.app",
    "https://www.surejan.app",
]
