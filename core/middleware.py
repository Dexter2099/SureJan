from django.conf import settings
from django.http import HttpResponseForbidden


def _client_ip(request):
    """Return the best-guess client IP address.

    Cloudflare exposes the original client IP in the CF-Connecting-IP header.
    Fall back to the standard X-Forwarded-For header and REMOTE_ADDR for
    environments without Cloudflare.
    """

    ip = request.META.get("HTTP_CF_CONNECTING_IP")
    if ip:
        return ip.strip()
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return (request.META.get("REMOTE_ADDR") or "").strip()


class AdminIPAllowlistMiddleware:
    """Restrict admin access to IPs in settings.ADMIN_IP_ALLOWLIST."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.prefix = "/" + settings.ADMIN_URL

    def __call__(self, request):
        allowlist = getattr(settings, "ADMIN_IP_ALLOWLIST", set())
        if allowlist and request.path.startswith(self.prefix):
            ip = _client_ip(request)
            if ip not in allowlist:
                return HttpResponseForbidden("Forbidden")
        return self.get_response(request)
