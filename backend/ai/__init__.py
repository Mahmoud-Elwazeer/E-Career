"""
AI services module for E-Career
Includes AWS Bedrock integration for CV parsing and job matching
"""

from .bedrock import bedrock_service

__all__ = ['bedrock_service']