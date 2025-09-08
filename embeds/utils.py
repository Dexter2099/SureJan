import logging
import requests
from requests.exceptions import HTTPError, Timeout

PLACEHOLDER_URL = "https://cdn.surejan.app/assets/placeholder.svg"

logger = logging.getLogger(__name__)


def get_thumbnail_url(url: str) -> str:
    """Return a thumbnail URL for ``url`` or a placeholder on failure.

    Fetches provider data using :func:`requests.get` with a five second timeout.
    Any :class:`HTTPError` or :class:`Timeout` results in ``PLACEHOLDER_URL``
    being returned and a warning being logged with the relevant status code or
    timeout reason.
    """
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("thumbnail_url", PLACEHOLDER_URL)
    except HTTPError as exc:
        status = getattr(getattr(exc, "response", None), "status_code", "unknown")
        logger.warning("Provider request failed with HTTP %s", status)
    except Timeout as exc:
        logger.warning("Provider request timed out: %s", exc)
    return PLACEHOLDER_URL
