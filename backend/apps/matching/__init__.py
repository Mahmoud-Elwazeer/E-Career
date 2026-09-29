"""Unified matching package.

Single authoritative matching interface that separates ELIGIBILITY from
RANKING from EXPLANATION (Phase D). Existing callers (profiles.MatchingService,
serializers, rashid tools) can delegate here so the platform stops producing
different match scores for the same (profile, job) on different pages.
"""
