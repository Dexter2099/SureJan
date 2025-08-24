from __future__ import annotations

import requests
from django.conf import settings

SAFE_BROWSING_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"


def check_url_safety(url: str) -> bool:
    """Return True if the URL is considered safe.

    Uses Google Safe Browsing Lookup API. If the API key is missing or the
    request fails for any reason, the URL is treated as safe.
    """
    api_key = getattr(settings, "URL_REPUTATION_API_KEY", "")
    if not api_key:
        return True

    payload = {
        "client": {"clientId": "surejan", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }

    try:
        resp = requests.post(
            SAFE_BROWSING_URL, params={"key": api_key}, json=payload, timeout=5
        )
        data = resp.json()
        return not data.get("matches")
    except Exception:
        # Fail open: if the reputation service is unavailable, don't block the URL
        return True
