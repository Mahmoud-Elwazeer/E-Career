from __future__ import annotations

from dataclasses import dataclass

import structlog

from apps.core.safe_fetch import safe_fetch, SSRFBlockedError

logger = structlog.get_logger()


@dataclass
class FreshnessResult:
    is_accessible: bool
    http_status: int | None
    is_closed: bool
    notes: list[str]


CLOSED_SIGNALS = [
    b"position has been filled",
    b"no longer accepting",
    b"job is closed",
    b"this role has been filled",
    b"expired",
    b"no longer available",
    b"this position is no longer",
]


class FreshnessCheckerStage:
    """Stage 5: Check if a job URL is still alive and the position is open."""

    TIMEOUT = 15

    def run(self, url: str) -> FreshnessResult:
        if not url:
            return FreshnessResult(
                is_accessible=False, http_status=None, is_closed=True, notes=["empty_url"]
            )

        notes = []
        try:
            result = safe_fetch(
                url,
                method="GET",
                timeout=self.TIMEOUT,
                allow_http=True,
                read_body=True,
            )
        except SSRFBlockedError as e:
            return FreshnessResult(
                is_accessible=False, http_status=None, is_closed=False,
                notes=[f"ssrf_blocked:{e.reason}"]
            )
        except Exception as e:
            return FreshnessResult(
                is_accessible=False, http_status=None, is_closed=False,
                notes=[f"error:{str(e)[:100]}"]
            )

        if result.status_code == 0:
            return FreshnessResult(
                is_accessible=False, http_status=None, is_closed=False,
                notes=[f"fetch_error:{result.error[:100]}"]
            )

        if result.status_code in (404, 410):
            return FreshnessResult(
                is_accessible=False,
                http_status=result.status_code,
                is_closed=True,
                notes=["page_gone"],
            )

        if result.status_code >= 400:
            return FreshnessResult(
                is_accessible=False,
                http_status=result.status_code,
                is_closed=False,
                notes=[f"http_error:{result.status_code}"],
            )

        is_closed = False
        content_lower = result.content[:5000].lower()
        for signal in CLOSED_SIGNALS:
            if signal in content_lower:
                is_closed = True
                notes.append(f"closed_signal:{signal.decode()}")
                break

        return FreshnessResult(
            is_accessible=True,
            http_status=result.status_code,
            is_closed=is_closed,
            notes=notes,
        )
