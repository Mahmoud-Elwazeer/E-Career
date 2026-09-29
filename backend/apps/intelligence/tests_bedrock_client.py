"""Tests for the centralized Bedrock client factory + failure classifier.

The classifier decides whether a failure is provider-level (retrying another
Bedrock model will NOT help — e.g. invalid credentials) vs model-level. Getting
this wrong causes retry storms and burns tokens/cost, so it is worth pinning.
No AWS calls are made — exceptions are constructed directly.
"""
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
)

from apps.intelligence.bedrock_client import (
    BedrockStatus,
    PROVIDER_LEVEL_FAILURES,
    classify_exception,
)


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": "x"}}, "InvokeModel")


def test_invalid_token_is_auth_failed():
    assert classify_exception(_client_error("UnrecognizedClientException")) == BedrockStatus.AUTH_FAILED
    assert classify_exception(_client_error("ExpiredTokenException")) == BedrockStatus.AUTH_FAILED


def test_access_denied():
    assert classify_exception(_client_error("AccessDeniedException")) == BedrockStatus.ACCESS_DENIED


def test_model_unavailable():
    assert classify_exception(_client_error("ResourceNotFoundException")) == BedrockStatus.MODEL_UNAVAILABLE
    assert classify_exception(_client_error("ValidationException")) == BedrockStatus.MODEL_UNAVAILABLE


def test_throttled():
    assert classify_exception(_client_error("ThrottlingException")) == BedrockStatus.THROTTLED


def test_no_credentials():
    assert classify_exception(NoCredentialsError()) == BedrockStatus.NO_CREDENTIALS


def test_network_error():
    exc = EndpointConnectionError(endpoint_url="https://bedrock-runtime.x.amazonaws.com")
    assert classify_exception(exc) == BedrockStatus.NETWORK_ERROR


def test_unknown_code_is_unknown():
    assert classify_exception(_client_error("SomeNewCode")) == BedrockStatus.UNKNOWN


def test_auth_and_creds_are_provider_level():
    # These must be treated as "don't retry other models" to avoid retry storms.
    assert BedrockStatus.AUTH_FAILED in PROVIDER_LEVEL_FAILURES
    assert BedrockStatus.NO_CREDENTIALS in PROVIDER_LEVEL_FAILURES
    assert BedrockStatus.REGION_INVALID in PROVIDER_LEVEL_FAILURES
    # Model-level failures are NOT provider-level.
    assert BedrockStatus.MODEL_UNAVAILABLE not in PROVIDER_LEVEL_FAILURES
    assert BedrockStatus.THROTTLED not in PROVIDER_LEVEL_FAILURES
