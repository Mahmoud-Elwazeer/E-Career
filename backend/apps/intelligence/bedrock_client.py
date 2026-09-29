"""Centralized AWS Bedrock client factory + classified health check.

Purpose (post-deploy hardening, 2026-09-29):
- ONE place that builds the Bedrock runtime client, so the pydantic-ai agent
  path and the BedrockLLMPlugin path share a coherent region + credential
  strategy instead of each constructing boto3 clients independently.
- A health check that CLASSIFIES failures so the platform can distinguish
  "credentials invalid" from "model unavailable" from "region problem", and
  never silently pretends AI is healthy while the provider is dead.

Security: never logs or returns secret values. Only reports where credentials
resolve from and a status category.
"""
from __future__ import annotations

import time
from enum import Enum

import boto3
import structlog
from botocore.config import Config
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    NoRegionError,
)
from django.conf import settings

logger = structlog.get_logger()


class BedrockStatus(str, Enum):
    HEALTHY = "HEALTHY"
    AUTH_FAILED = "AUTH_FAILED"
    ACCESS_DENIED = "ACCESS_DENIED"
    REGION_INVALID = "REGION_INVALID"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    THROTTLED = "THROTTLED"
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    NO_CREDENTIALS = "NO_CREDENTIALS"
    UNKNOWN = "UNKNOWN"


# Failure categories that mean "retrying another Bedrock model will NOT help" —
# used by the model router / circuit breaker to avoid retry storms.
PROVIDER_LEVEL_FAILURES = frozenset(
    {
        BedrockStatus.AUTH_FAILED,
        BedrockStatus.NO_CREDENTIALS,
        BedrockStatus.REGION_INVALID,
    }
)


def get_bedrock_region() -> str:
    return getattr(settings, "AWS_DEFAULT_REGION", None) or getattr(
        settings, "AWS_REGION", "us-east-1"
    )


def _boto_kwargs() -> dict:
    """Build boto3 kwargs. Explicit keys ONLY if configured; otherwise let the
    default provider chain (env, ~/.aws, EC2 instance role) resolve them."""
    kwargs: dict = {
        "region_name": get_bedrock_region(),
        "config": Config(
            retries={"max_attempts": 2, "mode": "standard"},
            connect_timeout=5,
            read_timeout=30,
        ),
    }
    access_key = getattr(settings, "AWS_ACCESS_KEY_ID", "") or ""
    secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", "") or ""
    # Only pass static keys if BOTH are present; otherwise fall through to the
    # default chain (this is what lets an EC2 instance role work).
    if access_key and secret_key:
        kwargs["aws_access_key_id"] = access_key
        kwargs["aws_secret_access_key"] = secret_key
        session_token = getattr(settings, "AWS_SESSION_TOKEN", "") or ""
        if session_token:
            kwargs["aws_session_token"] = session_token
    return kwargs


def get_runtime_client():
    """Return a bedrock-runtime client (for InvokeModel/Converse)."""
    return boto3.client("bedrock-runtime", **_boto_kwargs())


def get_control_client():
    """Return a bedrock control-plane client (for ListFoundationModels)."""
    return boto3.client("bedrock", **_boto_kwargs())


def credential_source() -> str:
    """Report WHERE credentials resolve from, without exposing values."""
    if (getattr(settings, "AWS_ACCESS_KEY_ID", "") or "") and (
        getattr(settings, "AWS_SECRET_ACCESS_KEY", "") or ""
    ):
        return "static_settings_env"
    try:
        creds = boto3.Session().get_credentials()
        if creds is None:
            return "none"
        return getattr(creds, "method", "default_chain") or "default_chain"
    except Exception:
        return "unknown"


def _classify(exc: Exception) -> BedrockStatus:
    if isinstance(exc, NoCredentialsError):
        return BedrockStatus.NO_CREDENTIALS
    if isinstance(exc, NoRegionError):
        return BedrockStatus.REGION_INVALID
    if isinstance(exc, EndpointConnectionError):
        return BedrockStatus.NETWORK_ERROR
    if isinstance(exc, ClientError):
        code = exc.response.get("Error", {}).get("Code", "")
        mapping = {
            "UnrecognizedClientException": BedrockStatus.AUTH_FAILED,
            "InvalidSignatureException": BedrockStatus.AUTH_FAILED,
            "AuthFailure": BedrockStatus.AUTH_FAILED,
            "ExpiredTokenException": BedrockStatus.AUTH_FAILED,
            "AccessDeniedException": BedrockStatus.ACCESS_DENIED,
            "ResourceNotFoundException": BedrockStatus.MODEL_UNAVAILABLE,
            "ValidationException": BedrockStatus.MODEL_UNAVAILABLE,
            "ThrottlingException": BedrockStatus.THROTTLED,
            "TooManyRequestsException": BedrockStatus.THROTTLED,
            "ModelTimeoutException": BedrockStatus.TIMEOUT,
        }
        return mapping.get(code, BedrockStatus.UNKNOWN)
    return BedrockStatus.UNKNOWN


def classify_exception(exc: Exception) -> BedrockStatus:
    """Public: classify a Bedrock exception into a BedrockStatus."""
    return _classify(exc)


def bedrock_health(probe_model: str | None = None) -> dict:
    """Run a cheap, real Bedrock probe and classify the result.

    Returns a secret-free dict: {status, region, credential_source, latency_ms,
    detail, model_probed}. Distinguishes auth vs region vs model vs throttle.
    """
    region = get_bedrock_region()
    src = credential_source()
    start = time.time()

    # Step 1: cheapest possible auth probe — list foundation models on the
    # control plane. This isolates credential/region validity from model access.
    try:
        client = get_control_client()
        client.list_foundation_models(byOutputModality="TEXT")
    except Exception as exc:  # noqa: BLE001 - we classify below
        status = _classify(exc)
        logger.warning(
            "bedrock_health_probe_failed",
            phase="list_models",
            status=status.value,
            region=region,
            credential_source=src,
        )
        return {
            "status": status.value,
            "region": region,
            "credential_source": src,
            "latency_ms": int((time.time() - start) * 1000),
            "detail": type(exc).__name__,
            "model_probed": None,
        }

    latency_ms = int((time.time() - start) * 1000)
    return {
        "status": BedrockStatus.HEALTHY.value,
        "region": region,
        "credential_source": src,
        "latency_ms": latency_ms,
        "detail": "list_foundation_models ok",
        "model_probed": probe_model,
    }
