"""
Secret resolution (directive Part XVII / XXXI).

Order of resolution:
  1. AWS Secrets Manager (if boto3 + a secret id are configured) — preferred in
     production; supports IAM access control + rotation.
  2. Environment variable fallback (for local/dev).

Secrets are NEVER logged, committed, or stored in the DB in plaintext. Callers
ask for a named key (e.g. "STRIPE_SECRET_KEY"); this module fetches it.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

from django.conf import settings


@lru_cache(maxsize=1)
def _aws_secret_bundle() -> dict:
    """Load a JSON secret bundle from AWS Secrets Manager, cached per process.

    Configure via settings.PAYMENTS_SECRET_ID (the Secrets Manager secret name).
    Returns {} if unavailable so env fallback can take over.
    """
    secret_id = getattr(settings, "PAYMENTS_SECRET_ID", "") or os.environ.get("PAYMENTS_SECRET_ID", "")
    if not secret_id:
        return {}
    try:
        import boto3  # boto3 is already a project dependency
        region = getattr(settings, "AWS_REGION", "") or os.environ.get("AWS_REGION", "eu-north-1")
        client = boto3.client("secretsmanager", region_name=region)
        resp = client.get_secret_value(SecretId=secret_id)
        raw = resp.get("SecretString") or "{}"
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        # Never crash the app because a secret store is unreachable; fall back.
        return {}


def get_secret(key: str, default: str = "") -> str:
    """Return a secret value by key (AWS bundle first, then env var)."""
    bundle = _aws_secret_bundle()
    if key in bundle and bundle[key]:
        return str(bundle[key])
    return os.environ.get(key, default)
