"""
AI financial workspace (directive Part XXXII).

Read-only. A deterministic intent parser maps an admin's natural-language
question to REAL analytics queries and returns the actual numbers plus their
source metrics and the period — it NEVER invents financial data. If Bedrock is
configured it may phrase a short natural-language summary OF the real numbers,
but the figures always come from the analytics layer, and the raw source data
is returned alongside so every answer is traceable.
"""
from __future__ import annotations

from datetime import timedelta
from django.utils import timezone

from . import analytics
from .references import Platform


_PLATFORM_WORDS = {
    "career": Platform.CAREER, "education": Platform.EDUCATION,
    "freelancing": Platform.FREELANCING, "kids": Platform.KIDS,
}


def answer(question: str) -> dict:
    """Return {answer, metrics, source, period} from real data only."""
    q = (question or "").lower()

    # Period
    since = None
    period = "all time"
    if "today" in q:
        since = timezone.now() - timedelta(days=1); period = "last 24h"
    elif "month" in q:
        since = timezone.now() - timedelta(days=30); period = "last 30 days"
    elif "week" in q:
        since = timezone.now() - timedelta(days=7); period = "last 7 days"

    # Platform filter
    platform = next((code for word, code in _PLATFORM_WORDS.items() if word in q), None)

    ov = analytics.financial_overview(platform_code=platform, since=since)

    # Intent → which metric to foreground
    if "fail" in q:
        metric = {"payments_failed": ov["payments_failed"], "success_rate": ov["payment_success_rate"]}
        headline = (f"{ov['payments_failed']} failed payment(s); success rate {ov['payment_success_rate']}% "
                    f"({period}{', '+platform if platform else ''}).")
    elif "refund" in q:
        metric = {"refunds_minor": ov["refunds"]}
        headline = f"Refunds total {ov['refunds']/100:.2f} ({period})."
    elif "revenue" in q or "made" in q or "earn" in q:
        metric = {"gross_minor": ov["gross_revenue"], "net_minor": ov["net_revenue"],
                  "by_platform": ov["revenue_by_platform"]}
        headline = (f"Gross revenue {ov['gross_revenue']/100:.2f}, net {ov['net_revenue']/100:.2f} "
                    f"({period}{', '+platform if platform else ''}).")
    elif "reconcil" in q or "mismatch" in q or "settlement" in q:
        rec = analytics.reconcile()
        metric = {"matched": rec["matched"], "exceptions": rec["exception_count"]}
        headline = f"Reconciliation: {rec['matched']} matched, {rec['exception_count']} exception(s)."
    else:
        metric = {"gross_minor": ov["gross_revenue"], "orders_paid": ov["orders_paid"],
                  "success_rate": ov["payment_success_rate"]}
        headline = (f"{ov['orders_paid']} paid order(s), gross {ov['gross_revenue']/100:.2f}, "
                    f"success rate {ov['payment_success_rate']}% ({period}).")

    return {
        "answer": headline,
        "metrics": metric,
        "source": {"query": "financial_overview", "platform": platform or "all", "period": period},
        "overview": ov,  # full traceable source data
    }
