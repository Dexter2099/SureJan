"""Shared HTTP client utilities."""

from __future__ import annotations

from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_SESSION: Optional[requests.Session] = None
_TIMEOUT = 5  # seconds
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def get_session() -> requests.Session:
    """Return a module-level session with retry and default headers."""
    global _SESSION
    if _SESSION is None:
        session = requests.Session()
        session.headers.update(_HEADERS)
        retries = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "HEAD", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        _SESSION = session
    return _SESSION


def fetch_json(url: str) -> dict:
    """Fetch ``url`` and return the parsed JSON response."""
    resp = get_session().get(url, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def fetch_html(url: str) -> requests.Response:
    """Fetch ``url`` and return the raw response object."""
    resp = get_session().get(url, timeout=_TIMEOUT)
    return resp
