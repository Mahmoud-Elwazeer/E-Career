"""
Seed the initial Legal/Privacy domain data: policy documents + v1 ACTIVE
versions, consent purposes, cookie categories, jurisdiction profiles, the
legal-entity singleton (left unconfigured), AI processing disclosures, and a
baseline retention matrix.

All legal TEXT below is written to reflect this platform's VERIFIED, real
behavior (confirmed in the Sept 2026 code audit — see
audit/LEGAL_PRIVACY_COMPLIANCE_MASTER.md) and VERIFIED, officially-sourced
facts about Egypt's PDPL (Law 151/2020 + Ministerial Decree 816/2025
Executive Regulations) and Saudi Arabia's PDPL (Royal Decree M/19, amended
M/148, SDAIA Implementing Regulations). Anything this command cannot verify
(the platform's actual legal entity name, registered address, DPO identity,
a legally-confirmed minors' age threshold, a confirmed refund window, confirmed
retention periods for several data categories) is deliberately left blank /
NULL with requires_legal_review=True — never invented. This is placeholder
legal CONTENT pending real legal counsel sign-off, not a finished policy.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.legal.models import (
    PolicyDocument, PolicyVersion, ConsentPurpose, CookieCategory,
    JurisdictionPolicyProfile, LegalEntityConfig, AIProcessingDisclosure,
    RetentionPolicy, ProcessorRecord,
)
from apps.legal import services


TERMS_MD = """# Terms of Service

**Status: DRAFT — REQUIRES LEGAL REVIEW / CONFIGURATION before this is a binding legal document.**

This page describes how the USAM Career platform ("USAM", "the platform", "we") works today, in plain
language, so job seekers and employers know what they're agreeing to. It is written to match the
platform's real, current behavior — it does not describe features that don't exist yet.

## 1. Who we are

The legal entity operating USAM Career is **REQUIRES LEGAL REVIEW / CONFIGURATION** (registered
address, company registration number, and tax ID are not yet configured — see Admin → Legal →
Entity Configuration).

## 2. What USAM does

USAM Career is a job-search and hiring platform. It aggregates and verifies job listings, lets job
seekers build profiles/CVs, apply to jobs, use AI-assisted tools (see our [AI Use & Rasheed
Disclosure](/legal/ai-disclosure)), and opt in to be discovered by employers through the Talent Pool.
Employers can post jobs, search for candidates (only those who opted in), and manage hiring pipelines.

## 3. Direct Apply — what it actually does

When a job listing shows a "Direct Apply" or "Apply" action, it takes you to the employer's own
application page or Applicant Tracking System (ATS) — it is a **redirect to a third party**, not an
application submitted on USAM's behalf, and does not imply any partnership, endorsement, or
employment relationship between USAM and that employer. USAM is not a party to your application and
does not guarantee a response from the employer.

## 4. Accounts

You must provide accurate information when creating an account. You're responsible for your account's
security (see our password/session practices in the [Security Overview](/legal/security)). You may
delete your account at any time from Settings; see our [Privacy Policy](/legal/privacy) for what
happens to your data when you do.

## 5. Talent Pool & visibility

Being discoverable in employer searches ("Talent Pool") is **off by default** and only happens if you
explicitly turn it on in Settings → Talent Pool Visibility. You can turn it off at any time.

## 6. AI features

Features like the Rasheed assistant, interview practice, and job-matching use AI/ML models. **AI
assists; it does not make final hiring decisions.** See the [AI Use & Rasheed Disclosure](/legal/ai-disclosure)
for details on what each AI feature does with your data.

## 7. Payments

If you purchase a paid plan, see our [Refund & Cancellation Policy](/legal/refunds) and
[Payment & Card Security Policy](/legal/payment-security). Prices are shown and charged in Egyptian
Pound (EGP) by default unless a specific transaction states otherwise.

## 8. Termination

We may suspend or terminate accounts that violate these terms. You may stop using the platform and
delete your account at any time.

## 9. Governing law

**REQUIRES LEGAL REVIEW / CONFIGURATION** — the governing jurisdiction and dispute-resolution process
have not yet been confirmed by legal counsel.

## 10. Changes to these terms

We version every change to this document. Material changes require you to re-accept before continuing
to use the platform. See the change history on this page.
"""

PRIVACY_MD = """# Privacy Policy

**Status: DRAFT — REQUIRES LEGAL REVIEW / CONFIGURATION before this is a finalized policy.**

This policy explains what personal data USAM Career actually collects and how it's actually used,
based on how the platform is built today. We do not claim compliance with any specific regulatory
framework in full; where a legal fact is not yet confirmed, we say so explicitly instead of guessing.

## 1. Who processes your data

**REQUIRES LEGAL REVIEW / CONFIGURATION** for the controller's legal entity name and contact details.
Our privacy contact (once configured) will be shown in the [Legal Center](/legal) and in Settings.

## 2. What we collect

- **Account data**: name, email, password (hashed), account type (individual/employer).
- **Profile & CV data**: career profile, skills, uploaded CV files, work history you provide.
- **Application data**: jobs you apply to and their status.
- **Talent Pool data**: only if you opt in via Settings — your profile becomes visible to verified
  employers in candidate search.
- **Interview practice data**: text/voice interview sessions, including transcripts, if you use the
  Interview Practice feature. Audio recordings are deleted after transcription; the transcript text is
  currently retained — see the retention matrix on this page for the configured period.
- **Payment data**: order/payment records (amount, currency, status) — **we never receive or store
  your card number, CVV, or other raw card data**; see [Payment & Card Security Policy](/legal/payment-security).
- **Cookies**: see our [Cookie Policy](/legal/cookies).
- **Usage/event data**: pages viewed, actions taken, for product analytics and security.

## 3. What we do NOT currently do

- We do not use third-party analytics or advertising trackers (no Google Analytics, Meta Pixel, or
  similar) as of this policy's effective date — confirmed by code audit.
- We do not sell personal data to third parties.
- We do not use AI to make a final hiring decision — see [AI Use & Rasheed Disclosure](/legal/ai-disclosure).

## 4. Legal bases / your rights

Depending on your jurisdiction, you may have rights to access, correct, delete, restrict, or export
your data, object to processing, and withdraw consent. Use the [Privacy Center](/app/privacy-center)
to exercise these rights — every request is logged and tracked to resolution.

## 5. Talent Pool & employer visibility

Your profile is **not visible to employers by default**. You opt in explicitly in Settings. Employers
only see profiles of candidates who opted in to the Talent Pool for the relevant search/role.

## 6. Retention

See the retention matrix maintained in our Admin Legal Control Plane and summarized here. Several
categories (e.g. interview transcripts) do not yet have a legally-confirmed retention period and are
marked "REQUIRES LEGAL REVIEW" until one is set.

## 7. International transfers

**REQUIRES LEGAL REVIEW / CONFIGURATION.** We maintain a processor and cross-border transfer register
(not yet publicly summarized here) and will update this section once legal counsel confirms current
transfer mechanisms (e.g. standard contractual clauses) for each processor.

## 8. Children's data

**REQUIRES LEGAL REVIEW / CONFIGURATION.** We do not currently enforce a minimum-age gate. A
legally-confirmed minimum age / guardian-consent threshold has not yet been set for this platform.

## 9. Contact

Use the [Privacy Center](/app/privacy-center) to submit a data request, or the contact details once
configured in the Legal Center.
"""

COOKIES_MD = """# Cookie Policy

We use a small number of cookies and local-storage items to run the platform. We respect your choice:
when you first visit, you can **Accept All**, **Reject Non-Essential**, or **Manage Preferences** to
choose exactly which categories you allow. You can change your choice at any time from the cookie
settings link in the footer. **Necessary cookies are never gated behind consent and never block
login** — the platform would not function without them.

## Categories

- **Strictly necessary** — session handling, security, and login state. Always on.
- **Functional** — remembers preferences like language and theme.
- **Analytics** — would help us understand usage patterns. **Not currently in active use** on this
  platform (confirmed by code audit: no analytics SDK is integrated as of this policy's effective
  date). The toggle exists so this is ready and governed the moment one is added — turning it on
  today has no effect.
- **Marketing** — would support ad/marketing measurement. **Not currently in active use.** Same as
  above: present for governance readiness, not because it does anything today.

## What we actually store today

Our current authentication tokens are stored in browser `localStorage`, not cookies (a detail flagged
in our security audit — see the [Security Overview](/legal/security)). This policy is written to
reflect that current reality, not an idealized architecture, and will be updated if that changes.
"""

REFUNDS_MD = """# Refund & Cancellation Policy

**Status: DRAFT — REQUIRES LEGAL REVIEW / CONFIGURATION for the refund window and legal entity.**

## Subscriptions

You can cancel a paid plan at any time from Billing. Whether cancellation takes effect immediately or
at the end of the current billing period depends on the specific plan's rules at the time of purchase
— we do not apply a one-size-fits-all cancellation rule.

## Refund window

The refund window is admin-configurable (see Admin → Legal → Entity Configuration) and is **not
hardcoded to any fixed number of days** in this policy. Until legal counsel confirms a window, this
section reads: **REQUIRES LEGAL REVIEW / CONFIGURATION — no refund window has been confirmed yet.**

## How refunds are processed

Approved refunds are issued through the same payment provider used for the original charge and are
recorded against the original transaction in our financial ledger — a refund never rewrites or deletes
the original payment record; it posts a new, linked reversing entry. You can see the status of a
refund in your account's billing/transaction history.

## Failed or declined payments

A failed or declined payment never grants access to a paid feature. If you were charged but did not
receive the entitlement you paid for, contact support through the Legal Center contact details (once
configured) or your Privacy Center.

## No invented trials or coupons

We do not advertise free trials or discount coupons on this page unless they are actually configured
and active in the platform at the time you read this.
"""

PAYMENT_SECURITY_MD = """# Payment & Card Security Policy

## What we never do

**USAM never receives, transmits, or stores your full card number (PAN), CVV/CVC, magnetic-stripe
data, or PIN.** This is a hard architectural rule, not a policy promise alone — confirmed in our code
audit: no field in our systems is named or holds a card number or CVV, and all currently-live checkout
flows redirect to a payment provider's own hosted payment page.

## How checkout actually works today

- Our active payment integration (Stripe) uses **provider-hosted Checkout** — you enter your card
  details directly on the provider's own page, never on a USAM-controlled form.
- A second provider integration (AlexBank) exists in our codebase but is **not live** — it is a
  scaffold that deliberately raises an error instead of ever processing a real payment, so it cannot
  accidentally take money in production. We do not claim AlexBank payments are available until this
  changes.
- We do not use raw `<input>` card number/CVV fields anywhere on the platform.

## Webhook security

Payment status changes are confirmed through server-to-server webhooks that we verify with the
provider's cryptographic signature before trusting them. We never update your subscription or order
status just because the browser told us "payment_success=true" — only a verified provider confirmation
does that. Each webhook event is deduplicated so a retried or replayed webhook can't be processed
twice.

## 3D Secure / strong authentication

Where required, 3D Secure (3DS) step-up authentication is handled entirely by our payment provider's
hosted flow — USAM does not implement its own 3DS logic.

## PCI DSS scope

Because card data never touches USAM's servers (provider-hosted checkout only), our PCI DSS exposure
is significantly reduced compared to a platform that collects card fields directly. **We do not claim
PCI DSS certification or any specific compliance level** — that determination requires a qualified
assessor, which has not yet occurred.

## No fake security badges

We do not display payment-security badges, certifications, or logos on this platform unless they are
genuinely held and verifiable.
"""

SECURITY_MD = """# Security Overview

This page describes real, verifiable security practices on the platform — not marketing claims. We do
not use phrases like "military-grade encryption" because they aren't meaningful technical claims.

## Authentication

- Passwords are hashed (never stored in plain text) and validated against common-password and
  similarity checks at signup.
- Session tokens are short-lived JSON Web Tokens (JWTs) with automatic rotation on refresh.
- **Known gap (tracked for remediation):** access/refresh tokens are currently stored in browser
  `localStorage` rather than an httpOnly cookie, which is more exposed to cross-site-scripting (XSS)
  than an httpOnly-cookie-based session. This is disclosed here rather than hidden.

## File security

- **Known gap (tracked for remediation):** CV and other uploaded documents are currently served from
  a predictable media URL without a signed-URL or per-request authorization check. We disclose this
  rather than claim a protection that isn't yet in place.

## Payments

See the [Payment & Card Security Policy](/legal/payment-security) — no raw card data is ever stored.

## Reporting a security issue

**REQUIRES LEGAL REVIEW / CONFIGURATION** — a dedicated security-contact address has not yet been
configured.
"""

AI_DISCLOSURE_MD = """# AI Use & Rasheed Disclosure

USAM uses AI/ML models in several features. This page lists them honestly, including what they do and
do not do.

## Rasheed (AI career coach / chat assistant)

Rasheed answers career questions, helps with CVs, and offers guidance. It is a conversational
assistant — **it does not make hiring decisions and has no authority over any employer's choices.**

## Job matching / recommendations

Our matching engine scores and ranks jobs against your profile to suggest relevant postings. **This is
a ranking/suggestion tool, not a hiring decision** — employers make their own decisions about who to
interview or hire.

## Interview practice (voice/text)

If you use voice interview practice, your audio is transcribed and then the raw audio file is deleted.
The transcript text is kept to show you feedback and history; see the retention matrix for how long.

## What AI does NOT do here

**AI does not make the final decision to hire, reject, or extend an offer to any candidate on this
platform.** Any such outcome is made by the employer, a human.
"""


class Command(BaseCommand):
    help = "Seed baseline Legal/Privacy domain data (policies, consent purposes, cookie categories, jurisdictions)."

    def handle(self, *args, **options):
        self._seed_documents()
        self._seed_consent_purposes()
        self._seed_cookie_categories()
        self._seed_jurisdictions()
        self._seed_ai_disclosures()
        self._seed_retention_matrix()
        self._seed_processors()
        LegalEntityConfig.load()  # ensure the singleton row exists, unconfigured
        self.stdout.write(self.style.SUCCESS("Legal domain seed complete."))

    def _seed_documents(self):
        docs = [
            ("terms", PolicyDocument.DocType.TERMS, "Terms of Service", TERMS_MD),
            ("privacy", PolicyDocument.DocType.PRIVACY, "Privacy Policy", PRIVACY_MD),
            ("cookies", PolicyDocument.DocType.COOKIES, "Cookie Policy", COOKIES_MD),
            ("refunds", PolicyDocument.DocType.REFUNDS, "Refund & Cancellation Policy", REFUNDS_MD),
            ("payment-security", PolicyDocument.DocType.PAYMENT_SECURITY, "Payment & Card Security Policy", PAYMENT_SECURITY_MD),
            ("security", PolicyDocument.DocType.SECURITY, "Security Overview", SECURITY_MD),
            ("ai-disclosure", PolicyDocument.DocType.AI_DISCLOSURE, "AI Use & Rasheed Disclosure", AI_DISCLOSURE_MD),
        ]
        for slug, doc_type, title, content in docs:
            doc, _ = PolicyDocument.objects.get_or_create(
                slug=slug, defaults={"doc_type": doc_type, "title": title},
            )
            if doc.versions.exists():
                self.stdout.write(f"Skip (already versioned): {slug}")
                continue
            version = PolicyVersion.objects.create(
                document=doc, version_label="2026.1", locale="en",
                jurisdiction="OTHER", status=PolicyVersion.Status.APPROVED,
                content_markdown=content,
                summary_of_changes="Initial draft published pending legal review.",
            )
            services.activate_version(version=version)
            self.stdout.write(f"Created + activated: {slug} v2026.1")

    def _seed_consent_purposes(self):
        purposes = [
            ("marketing_emails", ConsentPurpose.Category.MARKETING_EMAIL,
             "Marketing emails", "Promotional emails about new features, jobs, and offers.", False),
            ("marketing_sms", ConsentPurpose.Category.MARKETING_SMS,
             "Marketing SMS", "Promotional text messages.", False),
            ("talent_pool", ConsentPurpose.Category.TALENT_POOL,
             "Talent Pool visibility", "Let verified employers discover your profile in candidate search.", False),
            ("ai_processing", ConsentPurpose.Category.AI_PROCESSING,
             "AI-assisted processing", "Allow AI features (Rasheed, matching, interview practice) to process your profile/CV data.", False),
            ("cookie_analytics", ConsentPurpose.Category.COOKIE_ANALYTICS,
             "Analytics cookies", "Not currently in active use on this platform.", False),
            ("cookie_marketing", ConsentPurpose.Category.COOKIE_MARKETING,
             "Marketing cookies", "Not currently in active use on this platform.", False),
            ("cookie_functional", ConsentPurpose.Category.COOKIE_FUNCTIONAL,
             "Functional cookies", "Remembers preferences like language and theme.", False),
        ]
        for key, category, label, description, required in purposes:
            ConsentPurpose.objects.get_or_create(
                key=key,
                defaults={"category": category, "label": label, "description": description,
                         "is_required": required},
            )
        self.stdout.write("Consent purposes seeded.")

    def _seed_cookie_categories(self):
        cats = [
            (CookieCategory.Key.NECESSARY, "Strictly necessary",
             "Session handling, security, login state. Always on; cannot be rejected.", True),
            (CookieCategory.Key.FUNCTIONAL, "Functional",
             "Remembers preferences like language and theme.", False),
            (CookieCategory.Key.ANALYTICS, "Analytics",
             "Not currently in active use on this platform.", False),
            (CookieCategory.Key.MARKETING, "Marketing",
             "Not currently in active use on this platform.", False),
        ]
        for key, label, description, essential in cats:
            CookieCategory.objects.get_or_create(
                key=key, defaults={"label": label, "description": description, "is_essential": essential},
            )
        self.stdout.write("Cookie categories seeded.")

    def _seed_jurisdictions(self):
        # Facts below are from officially-sourced research (see master doc for
        # citations). SLA/age-threshold figures this platform cannot confirm
        # are intentionally left NULL with requires_legal_review=True.
        profiles = [
            dict(
                jurisdiction="EG", regulator_name="Personal Data Protection Centre (PDPC)",
                law_name="Law No. 151 of 2020 on the Protection of Personal Data "
                         "(Executive Regulations issued by Ministerial Decree No. 816 of 2025)",
                dsr_sla_days=6,  # Art. 32: 6 working days to reply to a rights request
                breach_notification_hours=72,
                minor_age_threshold=None,  # Children's data is "sensitive" under Art. 1; no single numeric age confirmed for guardian consent threshold
                requires_legal_review=True,
                source_notes=(
                    "Law 151/2020 (issued 13 Jul 2020, in force ~mid-Oct 2020); Executive "
                    "Regulations activated by Ministerial Decree 816/2025 (issued 1 Nov 2025, "
                    "effective 2 Nov 2025, one-year compliance period to 1 Nov 2026). DSR SLA: "
                    "Art. 32 — 6 working days. Breach notice to PDPC: within 72 hours (and to the "
                    "data subject 3 working days after PDPC notification). Children's data is "
                    "always 'sensitive personal data' per Art. 1; sensitive-data processing needs "
                    "PDPC licence + written explicit consent, plus guardian consent for a child's "
                    "data — but no single numeric 'minor' age is stated in the sources reviewed, "
                    "hence left blank pending legal confirmation."
                ),
            ),
            dict(
                jurisdiction="SA", regulator_name="Saudi Data & AI Authority (SDAIA)",
                law_name="Personal Data Protection Law (Royal Decree No. M/19 of 9/2/1443H, "
                         "amended by Royal Decree No. M/148 of 5/9/1444H) + SDAIA Implementing Regulations",
                dsr_sla_days=30,  # extendable once by up to 30 more days
                breach_notification_hours=72,
                minor_age_threshold=None,
                requires_legal_review=True,
                source_notes=(
                    "PDPL in force since 14 Sep 2023, fully enforceable since 14 Sep 2024 "
                    "(grace period ended). DSR SLA: 30 days, extendable once by up to 30 more "
                    "days with notice. Breach notice to SDAIA: within 72 hours via the National "
                    "Data Governance Platform. No specific numeric minors' age threshold "
                    "confirmed in the sources reviewed for this platform's context — left blank "
                    "pending legal confirmation."
                ),
            ),
        ]
        for data in profiles:
            JurisdictionPolicyProfile.objects.update_or_create(
                jurisdiction=data["jurisdiction"], defaults=data,
            )
        self.stdout.write("Jurisdiction profiles seeded (Egypt + Saudi Arabia).")

    def _seed_ai_disclosures(self):
        items = [
            ("rasheed_assistant", "Rasheed AI career coach",
             "Conversational AI assistant for career questions, CV help, and guidance.",
             "Chat messages, career profile context", False,
             "Conversation content is not readable by platform admins (privacy_mode)."),
            ("job_matching", "Job matching & recommendations",
             "Scores and ranks job postings against a candidate's profile to suggest relevant roles.",
             "Career profile, skills, job postings", False,
             "Used for ranking/suggestion only — does not decide hiring outcomes."),
            ("interview_practice", "Interview practice (voice/text)",
             "AI-driven mock interview sessions with transcription and feedback.",
             "Interview audio (deleted after transcription), transcript text, feedback", False,
             "Audio deleted post-transcription; transcript retention period pending legal review."),
            ("cv_parsing", "CV parsing & ATS scoring",
             "Extracts structured data from uploaded CVs and scores ATS-compatibility.",
             "Uploaded CV file contents", False, ""),
        ]
        for key, label, desc, cats, final_decision, retention in items:
            AIProcessingDisclosure.objects.get_or_create(
                feature_key=key,
                defaults={
                    "feature_label": label, "description": desc,
                    "data_categories_used": cats, "makes_final_decision": final_decision,
                    "retention_note": retention,
                },
            )
        self.stdout.write("AI processing disclosures seeded.")

    def _seed_retention_matrix(self):
        # Only categories with a genuinely confirmable period get a number.
        # Everything else is left unconfigured (NULL + requires_legal_review).
        rows = [
            ("account_core_data", "Email, name, account type", None, True,
             "No confirmed retention period yet — kept while the account is active; deletion flow exists via Privacy Center."),
            ("cv_documents", "Uploaded CV/resume files", None, True,
             "No confirmed retention period yet."),
            ("interview_transcripts", "Interview practice transcripts", None, True,
             "Known gap: no retention/TTL field exists in the interview models today (confirmed by code audit)."),
            ("payment_records", "Orders, payments, invoices, refunds (no card data)", None, True,
             "Financial record-keeping period not yet confirmed by legal/finance."),
            ("gdpr_export_files", "Generated data-export files", 30, False,
             "Confirmed in code: export files auto-delete 30 days after generation (accounts.DataExportRequest)."),
            ("account_deletion_grace", "Account deletion grace period", 30, False,
             "Confirmed in code: 30-day grace period before anonymization (accounts.AccountDeletionRequest)."),
        ]
        for category, description, days, requires_review, note in rows:
            RetentionPolicy.objects.get_or_create(
                data_category=category,
                defaults={
                    "description": description, "retention_period_days": days,
                    "requires_legal_review": requires_review, "legal_basis": note,
                },
            )

    def _seed_processors(self):
        """Seed ONLY vendors confirmed by actual code/infra in this
        repository — never a company merely because a client library is
        installed, and never a vendor assumed from a product category. Each
        entry's `data_categories`/`purpose` describes the REAL integration
        point found in code. `contract_reference`/`dpa_signed` are left
        blank/NULL (DPA status not confirmable from code — legal must
        confirm and fill these in) rather than assumed signed.
        """
        processors = [
            dict(
                name="Amazon Web Services (AWS)",
                purpose="Cloud infrastructure: S3 (CV/media/interview-audio storage), "
                        "Bedrock (AI model inference for Rasheed/matching/CV parsing), "
                        "Transcribe + Polly (voice interview speech-to-text/text-to-speech), "
                        "Secrets Manager (credential storage).",
                data_categories="CV/resume files, interview audio (deleted post-transcription), "
                                "AI prompt/response content, encrypted secrets",
                country="Varies by configured AWS region",
            ),
            dict(
                name="Stripe, Inc.",
                purpose="Payment processing via Stripe-hosted Checkout. Card data is "
                        "entered directly on Stripe's hosted page and never transits USAM's "
                        "servers.",
                data_categories="Order/payment metadata (amount, currency, reference) — "
                                "no card/PAN/CVV data",
                country="United States (Stripe's registered jurisdiction)",
            ),
            dict(
                name="Typesense",
                purpose="Full-text/faceted job search index (self-hosted or Typesense Cloud, "
                        "per deployment configuration).",
                data_categories="Job listing content (titles, descriptions, company names) — "
                                "not personal/candidate data",
                country="Depends on deployment (self-hosted vs. Typesense Cloud region)",
            ),
            dict(
                name="Sentry",
                purpose="Backend error tracking and performance monitoring "
                        "(sentry-sdk, server-side only — not a browser-loaded tracker).",
                data_categories="Error stack traces, request metadata; PII scrubbing "
                                "behavior depends on Sentry project configuration",
                country="Depends on configured Sentry region/plan",
            ),
        ]
        for data in processors:
            ProcessorRecord.objects.get_or_create(name=data["name"], defaults=data)
        self.stdout.write(
            "Processor register seeded (AWS, Stripe, Typesense, Sentry — confirmed by code). "
            "contract_reference/dpa_signed left unset for legal to confirm."
        )
        self.stdout.write("Retention matrix seeded.")
