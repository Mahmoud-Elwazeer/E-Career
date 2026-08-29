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
