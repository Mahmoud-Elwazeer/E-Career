"""
Launch-readiness evaluation for the Legal/Privacy/Payments domain.

This module answers one question honestly: "can this platform go live on
its legal/consent/privacy surface right now, and if not, why not?" It never
invents an answer — every check either passes, or reports a specific,
actionable reason it can't yet.

Output states (ordered worst-to-best; `overall_state` is the worst state any
individual check reports):

  BLOCKED               — a technical/safety invariant is violated (e.g. an
                           ACTIVE, publicly-served policy version still
                           contains an unresolved "REQUIRES LEGAL REVIEW /
                           CONFIGURATION" marker). This must never happen in
                           production and indicates something was activated
                           without going through proper review.
  CONFIGURATION_REQUIRED — an admin can fix this without legal counsel
                           (e.g. the legal entity singleton is blank, no
                           ACTIVE version exists yet for a core document).
  LEGAL_REVIEW_REQUIRED  — a real legal/business decision is needed before
                           launch (e.g. minor age threshold unconfirmed,
                           refund window unconfirmed, a RetentionPolicy row
                           still marked requires_legal_review=True).
  READY                  — every check above passed. This status is NEVER
                           equivalent to "fully compliant" — it only means
                           the known, checkable gaps this module is aware of
                           are closed. It does not replace legal counsel
                           sign-off.

No secrets (API keys, DB credentials, etc.) are read or exposed by this
module — only Legal-app domain data and a small number of settings values
that are not sensitive (PLATFORM_BASE_CURRENCY).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from django.conf import settings

import re

from .models import (
    PolicyDocument, PolicyVersion, CookieCategory, LegalEntityConfig, ProcessorRecord,
    JurisdictionPolicyProfile, RetentionPolicy,
)
from .services import UNRESOLVED_MARKER, UNRESOLVED_MARKER_AR  # single source of truth for the literals

# Core documents a launch cannot go live without an ACTIVE version of.
CORE_DOC_SLUGS = ["terms", "privacy", "cookies", "refunds", "payment-security"]

STATE_ORDER = ["READY", "LEGAL_REVIEW_REQUIRED", "CONFIGURATION_REQUIRED", "BLOCKED"]


# ── Placeholder scan (acceptance-pass item 14) ───────────────────────────────
# Patterns a genuinely-final, publicly-live policy version must never
# contain. Each entry is (name, compiled regex) — kept as plain, auditable
# patterns rather than a generic "lint" dependency, since this check only
# ever needs to run against this app's own PolicyVersion.content_markdown.
_PLACEHOLDER_PATTERNS = [
    # Deliberately specific template-placeholder phrasing (e.g. "[Insert
    # Company Name]", "[Your Company Name Here]", "[TODO: ...]") — NOT a
    # bare "your"/"company"/"site" word match, since real markdown link
    # text in this app's own policies legitimately contains brackets
    # (e.g. "[Your Data Rights](/legal/data-rights)" is a real cross-link,
    # not a placeholder) and a looser pattern would false-positive on it.
    ("bracket_placeholder", re.compile(
        r"\[(?:insert\b|TODO\b|TBD\b|placeholder\b|your (?:company|site) name|company name here|site name here)[^\]]*\]",
        re.IGNORECASE,
    )),
    ("todo_fixme", re.compile(r"\b(?:TODO|FIXME|XXX)\b")),
    ("lorem_ipsum", re.compile(r"\blorem ipsum\b", re.IGNORECASE)),
    ("example_email", re.compile(r"[\w.+-]+@(?:example\.(?:com|org|net)|test\.com|yourcompany\.(?:com|org))", re.IGNORECASE)),
    ("example_domain_url", re.compile(r"https?://[\w.-]*example\.(?:com|org|net)", re.IGNORECASE)),
    ("template_placeholder_ar", re.compile(r"\[(?:أدخل اسم|اسم الشركة هنا|اسم موقعك هنا)[^\]]*\]")),
]


def scan_version_for_placeholders(version: PolicyVersion) -> list[str]:
    """Return a list of human-readable findings for one PolicyVersion's
    content (both the unresolved-marker literals AND the broader
    placeholder-pattern scan below). Never mutates anything — read-only.
    """
    content = version.content_markdown or ""
    findings = []
    if UNRESOLVED_MARKER in content:
        findings.append(f"unresolved marker: '{UNRESOLVED_MARKER}'")
    if UNRESOLVED_MARKER_AR in content:
        findings.append(f"unresolved marker (ar): '{UNRESOLVED_MARKER_AR}'")
    for name, pattern in _PLACEHOLDER_PATTERNS:
        match = pattern.search(content)
        if match:
            findings.append(f"{name}: '{match.group(0)}'")
    return findings


def scan_active_versions_for_placeholders() -> dict[str, list[str]]:
    """Scan every currently-ACTIVE PolicyVersion (every locale) for
    unresolved markers/placeholder text. Returns {("slug", "locale"):
    [findings]} for any version with at least one finding — an empty dict
    means every ACTIVE version is clean. This is the one check in this
    module that matters most: DRAFT content is EXPECTED to contain
    placeholders (that's what DRAFT means); an ACTIVE, publicly-served
    version must never contain one. `activate_version()` already blocks
    the known unresolved-marker literals at activation time (services.py),
    but this function is the independent, after-the-fact verification
    sweep the directive separately asks for — it would also catch a
    placeholder pattern that isn't the literal marker string (e.g. a
    leftover '[TODO]' an editor typed directly into an already-ACTIVE
    version via a content edit, bypassing the activation chokepoint
    entirely since editing an ACTIVE version's content is a separate
    admin action from activating it).
    """
    results: dict[str, list[str]] = {}
    for version in PolicyVersion.objects.filter(status=PolicyVersion.Status.ACTIVE).select_related("document"):
        findings = scan_version_for_placeholders(version)
        if findings:
            results[f"{version.document.slug} ({version.locale})"] = findings
    return results


@dataclass
class ReadinessCheck:
    key: str
    state: str  # one of STATE_ORDER
    message: str


@dataclass
class ReadinessReport:
    checks: list = field(default_factory=list)

    @property
    def overall_state(self) -> str:
        if not self.checks:
            return "BLOCKED"
        worst_index = max(STATE_ORDER.index(c.state) for c in self.checks)
        return STATE_ORDER[worst_index]

    def add(self, key: str, state: str, message: str) -> None:
        self.checks.append(ReadinessCheck(key=key, state=state, message=message))


def _check_core_documents_active(report: ReadinessReport) -> None:
    for slug in CORE_DOC_SLUGS:
        doc = PolicyDocument.objects.filter(slug=slug).first()
        if doc is None:
            report.add(f"document.{slug}", "CONFIGURATION_REQUIRED",
                       f"PolicyDocument '{slug}' does not exist yet — run `manage.py seed_legal`.")
            continue
        active = doc.live_version
        if active is None:
            report.add(f"document.{slug}", "CONFIGURATION_REQUIRED",
                       f"'{slug}' has no ACTIVE version yet — review and activate a draft "
                       f"via the Admin Legal Control Plane.")
            continue
        active_content = active.content_markdown or ""
        if UNRESOLVED_MARKER in active_content or UNRESOLVED_MARKER_AR in active_content:
            report.add(f"document.{slug}", "BLOCKED",
                       f"'{slug}' has an ACTIVE version (v{active.version_label}, "
                       f"locale={active.locale}) that still contains an unresolved "
                       f"legal-review marker — this must never be publicly live. This "
                       f"indicates a version was activated without completing "
                       f"legal/configuration review.")
            continue
        report.add(f"document.{slug}", "READY", f"'{slug}' has a clean ACTIVE version.")


def _check_legal_entity(report: ReadinessReport) -> None:
    cfg = LegalEntityConfig.load()
    if not cfg.is_configured:
        report.add("legal_entity", "CONFIGURATION_REQUIRED",
                   "Legal entity name/address/privacy contact are not configured — "
                   "set them in Admin -> Legal -> Entity Configuration.")
        return
    if not cfg.privacy_contact_email and not cfg.support_contact_email:
        report.add("legal_entity", "CONFIGURATION_REQUIRED",
                   "Legal entity is configured but no contact email is set.")
        return
    report.add("legal_entity", "READY", "Legal entity is configured.")


def _check_refund_window(report: ReadinessReport) -> None:
    cfg = LegalEntityConfig.load()
    if cfg.default_refund_window_days is None:
        report.add("refund_window", "LEGAL_REVIEW_REQUIRED",
                   "No refund window has been legally confirmed yet "
                   "(LegalEntityConfig.default_refund_window_days is unset).")
        return
    report.add("refund_window", "READY", f"Refund window confirmed: "
               f"{cfg.default_refund_window_days} days.")


def _check_jurisdictions(report: ReadinessReport) -> None:
    for j_code, label in (("EG", "Egypt"), ("SA", "Saudi Arabia")):
        profile = JurisdictionPolicyProfile.objects.filter(jurisdiction=j_code).first()
        if profile is None:
            report.add(f"jurisdiction.{j_code}", "CONFIGURATION_REQUIRED",
                       f"No JurisdictionPolicyProfile exists for {label} — run `manage.py seed_legal`.")
            continue
        if profile.minor_age_threshold is None:
            report.add(f"jurisdiction.{j_code}.minor_age", "LEGAL_REVIEW_REQUIRED",
                       f"{label}: minor age / guardian-consent threshold is unconfirmed.")
        if profile.requires_legal_review:
            report.add(f"jurisdiction.{j_code}.review", "LEGAL_REVIEW_REQUIRED",
                       f"{label}: jurisdiction profile is still marked requires_legal_review.")
        if profile.dsr_sla_days and not profile.requires_legal_review:
            report.add(f"jurisdiction.{j_code}.sla", "READY",
                       f"{label}: DSR SLA confirmed at {profile.dsr_sla_days} days.")


def _check_processors(report: ReadinessReport) -> None:
    count = ProcessorRecord.objects.filter(is_active=True).count()
    if count == 0:
        report.add("processors", "CONFIGURATION_REQUIRED",
                   "No active processor register entries — run `manage.py seed_legal`.")
        return
    unconfirmed_dpa = ProcessorRecord.objects.filter(is_active=True, dpa_signed__isnull=True).count()
    if unconfirmed_dpa:
        report.add("processors.dpa", "LEGAL_REVIEW_REQUIRED",
                   f"{unconfirmed_dpa} of {count} active processor(s) have an unconfirmed "
                   f"DPA status (dpa_signed is NULL) — legal must confirm.")
    else:
        report.add("processors.dpa", "READY", "All active processors have a confirmed DPA status.")
    report.add("processors.register", "READY", f"{count} active processor(s) registered.")


def _check_cookie_categories(report: ReadinessReport) -> None:
    necessary = CookieCategory.objects.filter(key=CookieCategory.Key.NECESSARY, is_essential=True).first()
    if necessary is None:
        report.add("cookie_categories", "CONFIGURATION_REQUIRED",
                   "No essential 'necessary' cookie category configured — run `manage.py seed_legal`.")
        return
    report.add("cookie_categories", "READY", "Cookie categories configured.")


def _check_retention(report: ReadinessReport) -> None:
    pending = RetentionPolicy.objects.filter(requires_legal_review=True).count()
    total = RetentionPolicy.objects.count()
    if total == 0:
        report.add("retention", "CONFIGURATION_REQUIRED",
                   "No RetentionPolicy rows exist — run `manage.py seed_legal`.")
        return
    if pending:
        report.add("retention", "LEGAL_REVIEW_REQUIRED",
                   f"{pending} of {total} retention categories still require legal review "
                   f"(no confirmed retention_period_days). Enforcement for these categories "
                   f"stays disabled by design until confirmed.")
        return
    report.add("retention", "READY", f"All {total} retention categories have a confirmed period.")


def _check_placeholder_scan(report: ReadinessReport) -> None:
    findings = scan_active_versions_for_placeholders()
    if findings:
        report.add("placeholder_scan", "BLOCKED",
                   f"{len(findings)} ACTIVE policy version(s) contain unresolved "
                   f"placeholder text: {findings}. This must never be publicly "
                   f"live — see scan_active_versions_for_placeholders().")
        return
    report.add("placeholder_scan", "READY", "No ACTIVE policy version contains unresolved placeholder text.")


def _check_platform_currency(report: ReadinessReport) -> None:
    currency = getattr(settings, "PLATFORM_BASE_CURRENCY", None)
    if not currency:
        report.add("platform_currency", "CONFIGURATION_REQUIRED",
                   "PLATFORM_BASE_CURRENCY is not set.")
        return
    report.add("platform_currency", "READY", f"PLATFORM_BASE_CURRENCY={currency}.")


def check_legal_readiness() -> ReadinessReport:
    """Run every readiness check and return the aggregated report. Read-only
    — never mutates any Legal-app data."""
    report = ReadinessReport()
    _check_core_documents_active(report)
    _check_legal_entity(report)
    _check_refund_window(report)
    _check_jurisdictions(report)
    _check_processors(report)
    _check_cookie_categories(report)
    _check_retention(report)
    _check_platform_currency(report)
    _check_placeholder_scan(report)
    return report
