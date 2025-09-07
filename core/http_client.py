"""Shared HTTP client utilities."""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from typing import Optional
from urllib.parse import urlparse

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

logger = logging.getLogger(__name__)
# provider -> Counter(success=, error=)
COUNTERS: dict[str, Counter] = defaultdict(Counter)


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


def _log(url: str, source: str, status: int | None) -> None:
    provider = urlparse(url).netloc
    level = logging.INFO if status and status < 400 else logging.WARNING
    key = "success" if status and status < 400 else "error"
    COUNTERS[provider][key] += 1
    ua = get_session().headers.get("User-Agent", "")
    logger.log(
        level,
        "provider=%s url=%s source=%s ua=%s status=%s",
        provider,
        url,
        source,
        ua,
        status,
    )


def fetch_json(url: str, source: str = "unknown") -> dict:
    """Fetch ``url`` and return the parsed JSON response."""
    resp = get_session().get(url, timeout=_TIMEOUT)
    _log(url, source, getattr(resp, "status_code", None))
    resp.raise_for_status()
    return resp.json()


def fetch_html(url: str, source: str = "unknown") -> requests.Response:
    """Fetch ``url`` and return the raw response object."""
    resp = get_session().get(url, timeout=_TIMEOUT)
    _log(url, source, getattr(resp, "status_code", None))
    return resp
