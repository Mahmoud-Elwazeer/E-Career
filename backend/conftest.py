"""
Root-level conftest.py — makes fixtures from tests/conftest.py available
to all test paths (both apps/ and tests/).
Also disables DRF throttling during tests.
"""
import pytest


@pytest.fixture(autouse=True)
def _disable_throttling(settings):
    """Disable DRF throttling for all tests to avoid rate-limit interference."""
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }


def pytest_configure(config):
    """Disable throttling globally for the test session."""
    import django
    from django.conf import settings as django_settings
    # Ensure Django is set up before modifying settings
    try:
        django.setup()
    except RuntimeError:
        pass
    if hasattr(django_settings, "REST_FRAMEWORK"):
        django_settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
        django_settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}


from tests.conftest import *  # noqa: F401,F403,E402
