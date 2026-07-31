"""
Cohere Embedding Plugin via AWS Bedrock

Implementation of EmbeddingPlugin using Cohere Embed v3 via Bedrock.
"""

import json
import time
import structlog
from typing import List
from django.conf import settings

import boto3
from botocore.exceptions import ClientError

from .embedding_plugin import EmbeddingPlugin, EmbeddingRequest, EmbeddingResponse
from apps.events.emitter import emit
from apps.events.types import AI_MODEL_CALLED

logger = structlog.get_logger(__name__)


class CohereEmbedPlugin(EmbeddingPlugin):
    """Cohere Embed v3 via AWS Bedrock."""

    # Model costs per 1M tokens
    MODEL_COSTS = {
        "cohere.embed-english-v3": {"input_per_1k": 0.0001},
        "cohere.embed-multilingual-v3": {"input_per_1k": 0.0001},
    }

    MODEL_DIMENSIONS = {
        "cohere.embed-english-v3": 1024,
        "cohere.embed-multilingual-v3": 1024,
    }

    MODEL_ALIASES = {
        "cohere-embed-v3": "cohere.embed-english-v3",
        "cohere-embed-multilingual": "cohere.embed-multilingual-v3",
    }

    def __init__(self):
        self.region = getattr(settings, "AWS_DEFAULT_REGION", "us-east-1")
        self.access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID", None)
        self.secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)

        self.client = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
        )

    def generate(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings using Cohere via Bedrock."""
        start_time = time.time()

        # Resolve model alias
        model_id = self.MODEL_ALIASES.get(request.model, request.model)

        # Build request payload
        payload = {
            "texts": request.texts,
            "input_type": request.input_type,
            "truncate": "END",  # Truncate long texts from the end
        }

        try:
            # Invoke Bedrock
            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(payload),
            )

            # Parse response
            response_body = json.loads(response["body"].read())
            embeddings = response_body.get("embeddings", [])

            if not embeddings:
                raise ValueError("No embeddings returned from Bedrock")

            # Calculate cost
            tokens_used = sum(len(text.split()) for text in request.texts)  # Rough estimate
            cost_usd = self._calculate_cost(model_id, tokens_used)

            # Get dimensions
            dimensions = len(embeddings[0]) if embeddings else 0

            latency_ms = int((time.time() - start_time) * 1000)

            # Emit event for tracking
            emit(
                event_type=AI_MODEL_CALLED,
                category="ai",
                data={
                    "model": model_id,
                    "operation": "embed",
                    "texts_count": len(request.texts),
                    "tokens": tokens_used,
                    "latency_ms": latency_ms,
                    "cost_usd": cost_usd,
                    "dimensions": dimensions,
                },
            )

            logger.info(
                "cohere_embed_success",
                model=model_id,
                texts_count=len(request.texts),
                dimensions=dimensions,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
            )

            return EmbeddingResponse(
                embeddings=embeddings,
                model=model_id,
                dimensions=dimensions,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
            )

        except ClientError as e:
            logger.error("cohere_embed_bedrock_error", model=model_id, error=str(e))
            raise

        except Exception as e:
            logger.error("cohere_embed_failed", model=model_id, error=str(e))
            raise

    def _calculate_cost(self, model_id: str, tokens: int) -> float:
        """Calculate embedding cost."""
        if model_id in self.MODEL_COSTS:
            input_cost_per_1k = self.MODEL_COSTS[model_id]["input_per_1k"]
            return (tokens / 1000) * input_cost_per_1k
        return 0.0

    def get_dimensions(self, model: str) -> int:
        """Get dimension size for a model."""
        model_id = self.MODEL_ALIASES.get(model, model)
        return self.MODEL_DIMENSIONS.get(model_id, 1024)

    def health_check(self) -> dict:
        """Check if Bedrock is accessible."""
        try:
            # Try to invoke with a minimal request
            test_request = EmbeddingRequest(
                texts=["test"],
                model="cohere-embed-v3",
                input_type="search_query",
            )

            response = self.generate(test_request)

            return {
                "healthy": True,
                "provider": "bedrock_cohere",
                "dimensions": response.dimensions,
                "region": self.region,
            }

        except Exception as e:
            return {
                "healthy": False,
                "provider": "bedrock_cohere",
                "error": str(e),
                "region": self.region,
            }
