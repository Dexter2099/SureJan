from django.conf import settings
from django.http import HttpResponseForbidden


class AdminIPAllowlistMiddleware:
    """Restrict admin access to IPs in settings.ADMIN_IP_ALLOWLIST."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.prefix = "/" + settings.ADMIN_URL

    def __call__(self, request):
        allowlist = getattr(settings, "ADMIN_IP_ALLOWLIST", set())
        if allowlist and request.path.startswith(self.prefix):
            # Prefer X-Forwarded-For header if present (take first IP)
            ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
            if not ip:
                ip = request.META.get("REMOTE_ADDR", "")
            if ip not in allowlist:
                return HttpResponseForbidden("Forbidden")
        return self.get_response(request)
