"""Structured ingestion run metrics + rejection tracking (§2/§9/§20/§21).

Turns the silent `continue` funnel into observable, aggregated evidence so a
"154 fetched / 0 created" run is never invisible again. No permanent per-job
INFO spam — the tracker aggregates counts by reason and keeps a few samples
(including the FIRST real exception) for debugging.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any


# Canonical rejection reasons (stable strings for dashboards/alerts).
MISSING_APPLY_URL = "MISSING_APPLY_URL"
NOT_DIRECT_URL = "NOT_DIRECT_URL"
BLOCKED_AGGREGATOR = "BLOCKED_AGGREGATOR"
LOW_LEGITIMACY = "LOW_LEGITIMACY"
DUPLICATE = "DUPLICATE"
PERSISTENCE_ERROR = "PERSISTENCE_ERROR"
VERIFICATION_ERROR = "VERIFICATION_ERROR"
UNKNOWN = "UNKNOWN"


@dataclass
class RunMetrics:
    source: str = ""
    fetched: int = 0
    created: int = 0
    updated: int = 0
    verified: int = 0
    rejected: Counter = field(default_factory=Counter)
    samples: dict = field(default_factory=dict)

    def reject(self, reason: str, sample: Any = None) -> None:
        self.rejected[reason] += 1
        if reason not in self.samples and sample is not None:
            # Truncate large samples to keep logs bounded.
            self.samples[reason] = str(sample)[:500]

    def to_dict(self) -> dict:
        total_rejected = sum(self.rejected.values())
        return {
            "source": self.source,
            "fetched": self.fetched,
            "created": self.created,
            "updated": self.updated,
            "verified": self.verified,
            "rejected_total": total_rejected,
            "rejected": dict(self.rejected),
            "samples": self.samples,
        }

    @property
    def is_zero_yield_anomaly(self) -> bool:
        """§21: fetched a meaningful amount but persisted/updated nothing."""
        return self.fetched >= 10 and (self.created + self.updated) == 0
