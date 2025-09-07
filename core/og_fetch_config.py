"""Configuration for fetching Open Graph data."""

from __future__ import annotations

import os

OG_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

CONNECT_TIMEOUT = 5
READ_TIMEOUT = 8

OG_RETRY_STATUSES = {429, 502, 503, 504}

OG_FETCH_DISABLE_RETRIES = bool(os.getenv("OG_FETCH_DISABLE_RETRIES"))

__all__ = [
    "OG_HEADERS",
    "CONNECT_TIMEOUT",
    "READ_TIMEOUT",
    "OG_RETRY_STATUSES",
    "OG_FETCH_DISABLE_RETRIES",
]
