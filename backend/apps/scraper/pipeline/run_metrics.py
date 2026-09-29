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
NORMALIZATION_ERROR = "NORMALIZATION_ERROR"
LOW_LEGITIMACY = "LOW_LEGITIMACY"
DUPLICATE = "DUPLICATE"
PERSISTENCE_ERROR = "PERSISTENCE_ERROR"
VERIFICATION_ERROR = "VERIFICATION_ERROR"
UNKNOWN = "UNKNOWN"


@dataclass
class RunMetrics:
    source: str = ""
    provider: str = ""
    fetched: int = 0
    normalized: int = 0                 # passed contract validation
    created: int = 0
    updated: int = 0
    duplicates: int = 0                 # matched an existing job (subset of "handled")
    verified: int = 0                   # verification engine confirmed
    errors: int = 0                     # unexpected exceptions (not clean rejects)
    direct_apply_candidate: int = 0     # had a non-empty apply url to check
    direct_apply_verified: int = 0      # apply url passed the direct/moat gate
    publishable: int = 0               # created AND verified -> visible to users
    indexed: int = 0                    # pushed to the search index
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
            "provider": self.provider,
            "fetched": self.fetched,
            "normalized": self.normalized,
            "created": self.created,
            "updated": self.updated,
            "duplicates": self.duplicates,
            "verified": self.verified,
            "errors": self.errors,
            "direct_apply_candidate": self.direct_apply_candidate,
            "direct_apply_verified": self.direct_apply_verified,
            "publishable": self.publishable,
            "indexed": self.indexed,
            "rejected_total": total_rejected,
            "rejected": dict(self.rejected),
            "samples": self.samples,
        }

    @property
    def is_zero_yield_anomaly(self) -> bool:
        """§21: fetched a meaningful amount but persisted/updated nothing, and
        duplicates do NOT explain it (a run that only found existing jobs is
        healthy, not anomalous)."""
        handled = self.created + self.updated + self.duplicates
        return self.fetched >= 10 and handled == 0

    @property
    def is_degraded(self) -> bool:
        """§8/§9: fetched real volume but nothing became publishable and it
        wasn't just duplicates -> the source is DEGRADED and needs attention."""
        if self.fetched < 10:
            return False
        if (self.created + self.updated + self.duplicates) == 0:
            return True
        # Fetched a lot, but essentially everything got rejected and nothing is
        # publishable -> degraded even if a few dupes exist.
        return self.publishable == 0 and self.created == 0
