"""
Compatibility shim for apps.ai.bedrock imports.

Delegates to the root ai.bedrock module which itself delegates to apps.intelligence.
"""
from ai.bedrock import BedrockService, bedrock_service

__all__ = ['BedrockService', 'bedrock_service']
