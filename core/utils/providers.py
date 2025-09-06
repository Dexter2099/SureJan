from __future__ import annotations

"""Utilities for determining media provider names from domains."""

# Mapping of known domains to their provider display names.
_PROVIDER_MAP = {
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "x.com": "X",
    "twitter.com": "X",
    "rumble.com": "Rumble",
}


def provider_from_domain(domain: str) -> str:
    """Return a human-friendly provider name for ``domain``.

    If the domain is not recognised, the domain itself is returned.
    ``None`` or empty strings return an empty string.
    """
    if not domain:
        return ""
    domain = domain.lower().split(":", 1)[0]
    if domain.startswith("www."):
        domain = domain[4:]
    for key, name in _PROVIDER_MAP.items():
        if domain == key or domain.endswith("." + key):
            return name
    return domain
