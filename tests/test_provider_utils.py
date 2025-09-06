from core.utils.providers import provider_from_domain


def test_provider_from_domain_known():
    assert provider_from_domain("www.youtube.com") == "YouTube"
    assert provider_from_domain("youtu.be") == "YouTube"
    assert provider_from_domain("twitter.com") == "X"
    assert provider_from_domain("subdomain.rumble.com") == "Rumble"


def test_provider_from_domain_unknown():
    assert provider_from_domain("example.com") == "example.com"
    assert provider_from_domain("") == ""
