"""Shared HTTP client utilities."""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
import random
import time
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib import robotparser
from urllib3.util.retry import Retry

from .og_fetch_config import (
    CONNECT_TIMEOUT,
    OG_FETCH_DISABLE_RETRIES,
    OG_HEADERS,
    OG_RETRY_STATUSES,
    READ_TIMEOUT,
)

_SESSION: Optional[requests.Session] = None
_OG_SESSION: Optional[requests.Session] = None
_ROBOTS: dict[str, robotparser.RobotFileParser] = {}

logger = logging.getLogger(__name__)
# provider -> Counter(success=, error=)
COUNTERS: dict[str, Counter] = defaultdict(Counter)


def get_session() -> requests.Session:
    """Return a module-level session with retry and default headers."""
    global _SESSION
    if _SESSION is None:
        session = requests.Session()
        session.headers.update(OG_HEADERS)

        if not OG_FETCH_DISABLE_RETRIES:
            retries = Retry(
                total=2,
                backoff_factor=0.5,
                status_forcelist=list(OG_RETRY_STATUSES),
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
    resp = get_session().get(url, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
    _log(url, source, getattr(resp, "status_code", None))
    resp.raise_for_status()
    return resp.json()


def fetch_html(url: str, source: str = "unknown") -> requests.Response:
    """Fetch ``url`` and return the raw response object."""
    resp = get_session().get(url, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
    _log(url, source, getattr(resp, "status_code", None))
    return resp


def get_og_session() -> requests.Session:
    """Return a session for OG fetching without built-in retries."""
    global _OG_SESSION
    if _OG_SESSION is None:
        session = requests.Session()
        session.headers.update(OG_HEADERS)
        _OG_SESSION = session
    return _OG_SESSION


def _robots_allowed(url: str) -> bool:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    parser = _ROBOTS.get(base)
    if parser is None:
        parser = robotparser.RobotFileParser()
        parser.set_url(urljoin(base, "/robots.txt"))
        try:
            parser.read()
        except Exception:
            pass
        _ROBOTS[base] = parser
    ua = OG_HEADERS.get("User-Agent", "*")
    return parser.can_fetch(ua, url)


def fetch_og_html(
    url: str, source: str = "unknown", fallback: bool = False
) -> requests.Response:
    """Fetch ``url`` for OpenGraph scraping with retries and robots checks."""

    provider = urlparse(url).netloc
    if not _robots_allowed(url):
        _log(url, source, None)
        logger.warning(
            "provider=%s url=%s reason=robots fallback=%s", provider, url, fallback
        )
        raise PermissionError("Blocked by robots.txt")

    session = get_og_session()
    attempts = 1 if OG_FETCH_DISABLE_RETRIES else 3
    resp: Optional[requests.Response] = None
    last_exc: Optional[Exception] = None

    for attempt in range(1, attempts + 1):
        try:
            resp = session.get(url, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
            status: Optional[int] = resp.status_code
        except requests.exceptions.Timeout as exc:
            last_exc = exc
            status = None

        logger.info(
            "provider=%s url=%s status=%s attempt=%s",
            provider,
            url,
            status if status is not None else "timeout",
            attempt,
        )

        if status is not None and (status not in OG_RETRY_STATUSES or status in {403, 404}):
            _log(url, source, status)
            if status >= 400:
                logger.warning(
                    "provider=%s url=%s reason=http_%s fallback=%s",
                    provider,
                    url,
                    status,
                    fallback,
                )
            return resp

        if attempt == attempts:
            _log(url, source, status if resp is not None else None)
            reason = "timeout" if status is None else f"http_{status}"
            logger.warning(
                "provider=%s url=%s reason=%s fallback=%s",
                provider,
                url,
                reason,
                fallback,
            )
            if resp is not None:
                return resp
            raise last_exc if last_exc else Exception("fetch failed")

        time.sleep(random.uniform(0.2, 0.3))
        backoff = (0.5 if attempt == 1 else 1.5) + random.uniform(-0.25, 0.25)
        time.sleep(max(backoff, 0))

    return resp  # pragma: no cover
