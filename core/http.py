"""HTTP helper utilities."""

from functools import wraps
from urllib.parse import quote

from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth.views import redirect_to_login


def login_required_htmx(view):
    """Require login with HTMX-aware handling.

    If the user is authenticated, the wrapped view is called. For anonymous
    HTMX requests a ``401`` response is returned with an ``HX-Redirect`` header
    pointing at the login page. Normal anonymous requests are redirected to the
    login page using :func:`redirect_to_login`.
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view(request, *args, **kwargs)

        if request.headers.get("HX-Request") == "true":
            resp = HttpResponse(status=401)
            login_url = reverse("login") + "?next=" + quote(request.get_full_path())
            resp["HX-Redirect"] = login_url
            return resp

        return redirect_to_login(request.get_full_path())

    return wrapper

