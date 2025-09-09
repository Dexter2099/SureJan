"""Expose view functions and classes for the core app."""

from django.core.exceptions import RequestDataTooBig
from django.http import HttpResponseBadRequest
from django.shortcuts import render

from .posts import (
    preview_markdown,
    markdown_preview,
    mission,
    anti_astroturf,
    _cached_post_signals,
    post_signals_json,
    render_preview,
    feed_list,
    home,
    post_submit,
    post_detail,
    post_detail_id,
    post_edit,
    post_delete_owner,
)
from .users import (
    SignupForm,
    RateLimitedLoginView,
    signup,
    recovery_codes,
    download_recovery_codes,
    regenerate_recovery_codes,
    _get_profile_user,
    user_overview,
    user_comments,
    user_submitted,
    ban_user,
    unban_user,
)
from .moderation import (
    mod_astro,
    transparency_methods,
    transparency_posts,
    post_delete,
    post_remove,
    post_lock,
    post_slowmode,
    post_domain_throttle,
)
from .reports import (
    report,
    report_list,
)


def disallowed_host(request, exception=None):
    """Render a friendly message for disallowed host errors."""
    return HttpResponseBadRequest("Unknown host—check the URL")


def _error_template(request, code):
    """Return full or HTMX partial error template path."""
    if request.headers.get("HX-Request") == "true":
        return f"errors/partials/{code}.html"
    return f"errors/{code}.html"


def handler400(request, exception=None):
    """Render 400 Bad Request page."""
    return render(request, _error_template(request, 400), status=400)


def handler403(request, exception=None):
    """Render 403 Forbidden page."""
    return render(request, _error_template(request, 403), status=403)


def handler404(request, exception=None):
    """Render 404 Not Found page."""
    return render(request, _error_template(request, 404), status=404)


def handler500(request):
    """Render 500 Server Error page."""
    return render(request, _error_template(request, 500), status=500)


def handler429(request, exception=None):
    """Render 429 Too Many Requests page."""
    return render(request, _error_template(request, 429), status=429)


def request_too_big(request, exception: RequestDataTooBig | None = None):
    """Render 413 Request Entity Too Large page."""
    return render(request, _error_template(request, 413), status=413)
