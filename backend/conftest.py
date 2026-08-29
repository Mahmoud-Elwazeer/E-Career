"""
Root-level conftest.py — makes fixtures from tests/conftest.py available
to all test paths (both apps/ and tests/).
Also disables DRF throttling during tests.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
django.setup()

import pytest  # noqa: E402
from tests.conftest import *  # noqa: F401,F403,E402


@pytest.fixture(autouse=True)
def _disable_throttling(settings):
    """Disable DRF throttling for all tests to avoid rate-limit interference."""
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
