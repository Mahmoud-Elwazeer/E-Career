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

Every purchase on this platform today is a **single, one-time charge** that activates a plan — there
is no automatic recurring billing or auto-renewal. If you want to extend or renew a plan, you make a
new purchase when you're ready; there is nothing to "cancel" to stop a future charge, because no
future charge is ever scheduled by this platform. If a feature granted by a purchase needs to be
adjusted (e.g. deactivated early), contact support through the Legal Center contact details (once
configured) or your Privacy Center — this is currently an admin-assisted action, not a self-service
toggle.

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

USAM Career is committed to protecting the privacy and security of your financial and personal
information. This policy explains how we collect, use, and protect your payment data when you carry
out transactions on our site, jobs.usamif.com.

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

- All CV, resume, and ownership-claim document uploads are checked for file type, size, and
  content-type spoofing (magic-byte verification), and scanned for malware before being accepted or
  processed — this applies to every upload path that accepts this kind of file, not just the primary
  one.
- When an employer views an applicant's CV through the employer dashboard, that request is
  authorization-checked every time (confirmed: the employer must currently have a legitimate
  relationship to that specific application) — an employer cannot view another employer's
  applicants' files.
- **Known gap (tracked for remediation):** the underlying file storage is not yet backed by
  expiring, signed URLs. If a CV file's raw storage URL is ever directly obtained outside the
  authorization-checked flow above, that URL itself does not expire or re-check identity on each
  request. We disclose this rather than claim a protection that isn't yet in place.

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

# ── Added in the 2026-09-21 continuation pass ────────────────────────────────
# Six new documents closing real route/disclosure gaps found by comparing
# this repo's prior 7-document set against the supplemental legal specs
# (see audit/LEGAL_PRIVACY_COMPLIANCE_MASTER.md §9A, continuation entry).
# Each addresses something the existing 7 documents do NOT already cover —
# none of this duplicates Terms/Privacy/Refunds/Payment-Security content.

ACCEPTABLE_USE_MD = """# Acceptable Use Policy

This page states what you may not do on USAM Career, separate from the general [Terms of
Service](/legal/terms) — so the rules are easy to find on their own, not buried in a longer document.

## Prohibited uses

- Scraping, bulk-downloading, or systematically harvesting job listings, candidate profiles, or any
  other platform data outside the APIs/exports we provide for that purpose.
- Creating fake accounts, fake job postings, or fake applications.
- Uploading malware, or a CV/document crafted to exploit a file-parsing vulnerability (every upload is
  scanned — see [Security Overview](/legal/security) — but attempting this is still prohibited
  regardless of whether the scan catches it).
- Attempting to bypass or disable the Talent Pool visibility setting of another user, or accessing a
  candidate's data without a legitimate relationship to their application.
- Circumventing or interfering with the platform's **direct-application verification** behavior
  (see below).

## Direct-application verification — a real, enforced rule, not just a policy statement

USAM's job-ingestion pipeline is built to reject apply links that route through a third-party
application aggregator or "apply" intermediary (e.g. a generic aggregator apply-redirect page) rather
than the employer's own site or Applicant Tracking System (ATS) — this is enforced in code at
ingestion time (jobs resolving to a known aggregator domain are classified `BLOCKED_AGGREGATOR` and
excluded), not merely stated as an intention. Job sources that persistently resolve to blocked
domains are deactivated. If you believe a listing on USAM routes through such an intermediary anyway,
report it — this is treated as a product defect, not an acceptable outcome.

## Employer-specific conduct

Employers may only search/contact candidates who have opted in to Talent Pool visibility, and may only
view applicant data for applications submitted to that employer's own postings — both are enforced
server-side (see [Security Overview](/legal/security) §"File security" for the applicant-CV
authorization check specifically).

## Enforcement

We may suspend or terminate an account that violates this policy, consistent with the [Terms of
Service](/legal/terms) §8.
"""

DATA_RIGHTS_MD = """# Your Data Rights

This page explains, in plain language, what rights you have over your personal data on USAM Career
and exactly how to exercise them — as a standalone explainer, not only inside the longer [Privacy
Policy](/legal/privacy).

## What you can do today, right now

All of the following are available self-service from the [Privacy Center](/app/privacy-center):

- **Access** — request an export of the personal data we hold about you.
- **Correct** — update your profile/CV/account data directly in Settings at any time.
- **Delete** — request account deletion. We apply a 30-day grace period (so an accidental or
  compromised-account deletion request can be cancelled) before deletion actually executes; you can
  cancel the pending deletion at any time during that window from the Privacy Center.
- **Withdraw consent** — turn off Talent Pool visibility or marketing emails at any time; each is
  tracked as its own independent, append-only consent record, never bundled with your Terms
  acceptance.
- **Object / request review** — open a formal Data Subject Request (DSR) from the Privacy Center for
  anything not covered by the self-service actions above; every DSR is tracked to a status and has a
  due date computed from your jurisdiction's confirmed regulatory SLA where one has been confirmed
  (see [Jurisdictions](/legal) research in our compliance records) — **REQUIRES LEGAL REVIEW /
  CONFIGURATION** for the exact SLA number shown to you until legal confirms it for your specific
  situation.

## Request status tracking

Every DSR you open shows a real, append-only event history (not just a single status flag) — you can
see exactly when it moved between stages.

## What this page does not do

It does not claim a right that doesn't apply to your jurisdiction (e.g. data portability is not a
right in every jurisdiction we currently serve — see the jurisdiction-specific research referenced in
our compliance records), and it does not promise a response time this platform cannot actually commit
to in code.
"""

SUBPROCESSORS_MD = """# Sub-processor Disclosure

A sub-processor is a vendor that processes personal data on USAM Career's behalf. This page lists the
ones actually integrated in our systems — confirmed by code audit, never assumed from a vendor
category or an installed client library alone.

## Current sub-processors

- **Amazon Web Services (AWS)** — cloud infrastructure and AI model-hosting substrate: object storage
  for CVs/media/interview audio, the Bedrock model-serving path used by the Rasheed assistant and
  related AI features, Transcribe/Polly for voice interview practice, and Secrets Manager for
  credential storage.
- **Stripe, Inc.** — our live, hosted payment checkout provider. See [Payment & Card Security
  Policy](/legal/payment-security) for how this integration actually works.
- **Typesense** — search indexing. Deployed as a self-hosted container by default in this platform's
  infrastructure; it is only a true third-party sub-processor if a deployment is configured to point
  at Typesense Cloud instead of a self-managed instance.
- **Sentry** — backend error tracking (server-side only; not a browser/user-facing tracker).

## What this page does not claim

**Data Processing Agreement (DPA) status for each vendor is marked "not yet confirmed" rather than
assumed signed or unsigned** — this is a `dpa_signed = NULL` field in our internal register, visible to
admins, and requires legal/procurement confirmation per vendor. This page will be updated once that
confirmation exists, not before.

## AI model path note

Rasheed and other AI features run on AWS Bedrock, which hosts the underlying model. Depending on the
model configured, the model provider (e.g. Anthropic) is a **model-hosting path reached entirely
through AWS's infrastructure boundary**, not a separate sub-processor USAM contracts with directly —
USAM's data does not leave AWS to reach the model provider as an independent counterparty under the
current architecture. See [AI Use & Rasheed Disclosure](/legal/ai-disclosure) for what each AI feature
does with your data.
"""

INTERNATIONAL_TRANSFERS_MD = """# International Data Transfers

This page discloses, honestly, what we currently know and do not yet know about cross-border transfers
of personal data on USAM Career.

## What we can confirm today

Our infrastructure sub-processors (see [Sub-processor Disclosure](/legal/subprocessors)) may process
or store data in regions outside Egypt and Saudi Arabia, depending on how each service is configured.
We maintain an internal cross-border transfer register tracking, per transfer: the destination
country, the data categories involved, and the legal safeguard mechanism relied upon (e.g. Standard
Contractual Clauses, an adequacy decision, or explicit consent).

## What is REQUIRES LEGAL REVIEW / CONFIGURATION

**No specific transfer in our register currently has a confirmed safeguard mechanism or legal
authorization reference** — our register defaults every entry to "not yet determined" rather than
assuming Standard Contractual Clauses or any other mechanism applies by default. This matters because:

- **Egypt's Personal Data Protection Law** requires prior authorization from the Personal Data
  Protection Centre (PDPC) **plus** the data subject's explicit consent for every outbound transfer,
  even to a destination otherwise considered adequate — there is currently no published PDPC adequacy
  list we can rely on.
- **Saudi Arabia's PDPL** requires an approved safeguard (Standard Contractual Clauses, Binding Common
  Rules, certification, or case-by-case approval), and a Data Transfer Risk Assessment for
  sensitive/large-scale continuous transfers.

Until legal counsel confirms the applicable mechanism for each real transfer our infrastructure
performs, this page will continue to say so explicitly rather than assert a safeguard is in place when
it has not been formally confirmed.
"""

CANDIDATE_PRIVACY_MD = """# Candidate Privacy Notice

This notice is specifically for job seekers applying to a role on USAM Career — surfaced at the point
you apply, not only inside the general [Privacy Policy](/legal/privacy), because what happens to your
application data is a decision you should be able to see before you submit it.

## What happens when you apply

- Your application (profile data, CV, and any custom-form answers the employer's posting asks for) is
  shared with **that specific employer only** — not with any other employer, and not added to the
  public Talent Pool search just because you applied.
- If the listing uses **Direct Apply**, clicking it takes you to the employer's own site or Applicant
  Tracking System — USAM is not a party to that application and does not control what happens to your
  data once you're on the employer's own system; see [Acceptable Use Policy](/legal/acceptable-use)
  for how our ingestion pipeline enforces, at a code level, that these are genuine employer/ATS
  links rather than third-party aggregator intermediaries.
- If the listing uses USAM's own in-platform application form, your submission is stored as an
  application record tied to that job and that employer's account, with server-side authorization
  checks on every view (an employer can only see applicants to their own postings).

## Talent Pool is separate from applying

Applying to a specific job is **not** the same as opting into the Talent Pool (general employer
candidate search). Talent Pool visibility stays off unless you separately turn it on in Settings —
applying to one job never silently opts you into being discoverable for others.

## AI involvement in your application

If job matching/ranking features were involved in surfacing this listing to you, or if an employer
uses ranking tools against their own applicant pool, **a human employer makes the actual hiring
decision** — see [AI Use & Rasheed Disclosure](/legal/ai-disclosure).

## Your rights over this data

See [Your Data Rights](/legal/data-rights) and the [Privacy Center](/app/privacy-center) for access,
correction, deletion, and consent-withdrawal options — these apply to application data the same as any
other personal data we hold about you.
"""

BUSINESS_TERMS_MD = """# Employer & Business Terms

These terms apply specifically to employer/company accounts on USAM Career, in addition to the general
[Terms of Service](/legal/terms).

## What an employer account can do

- Post job listings.
- Search and contact candidates who have explicitly opted in to Talent Pool visibility — **only**
  those candidates; an employer cannot search or view a candidate who has not opted in.
- View and manage applications submitted to that employer's own postings — access to applicant data is
  authorization-checked on every request (an employer cannot view another employer's applicants).
- Manage a team of users under the same company account, subject to whatever role/permission controls
  exist on the employer's plan.

## Verification

Job postings and the Direct Apply links associated with them are checked against the employer's own
domain where applicable, as part of this platform's effort to keep "Direct Apply" meaning a genuine
employer/ATS link rather than a third-party intermediary — see [Acceptable Use
Policy](/legal/acceptable-use).

## Billing

Employer plans are purchased the same way as individual plans: a single one-time charge per purchase,
no automatic recurring billing. See [Refund & Cancellation Policy](/legal/refunds) and [Payment & Card
Security Policy](/legal/payment-security) for details that apply equally to employer and individual
purchases — there is no separate billing engine or separate refund process for employer accounts.

## Candidate data obligations

An employer account holder must handle candidate data obtained through USAM (applications, Talent Pool
search results) consistently with applicable data protection law and must not redistribute candidate
personal data to a third party outside the purpose of evaluating that candidate for the role they
applied to or were sourced for. USAM's own technical controls (see [Security
Overview](/legal/security)) do not, by themselves, make an employer's own downstream handling of that
data compliant — that remains the employer's own responsibility.

## Termination

We may suspend or terminate an employer account for violating this policy or the general [Terms of
Service](/legal/terms) §8.
"""


# ── Arabic (ar) locale content — 2026-09-21 continuation pass ───────────────
# Unreviewed machine translation of the English documents above, seeded with
# is_machine_translated=True (never silently presented as an official
# equivalent — directive-mandated flag, enforced by the model/serializer).
# Condensed relative to the English originals (same key facts and the same
# REQUIRES LEGAL REVIEW / CONFIGURATION markers, not expanded prose) — this
# keeps translation effort proportionate while still being genuine, reviewable
# content rather than an empty placeholder. A qualified legal/Arabic reviewer
# must review and, if needed, replace this before it is ever activated in
# production (the DRAFT-by-default + is_machine_translated flag make this
# unmistakable to a reviewer).
AR_TRANSLATIONS = {
    "terms": """# شروط الخدمة

**الحالة: مسودة — تتطلب مراجعة قانونية / تهيئة قبل أن تصبح وثيقة قانونية ملزمة.**

**ترجمة آلية غير مراجعة.** هذه الصفحة تصف كيفية عمل منصة USAM Career فعلياً اليوم.

## 1. من نحن

الكيان القانوني المُشغِّل لـ USAM Career **يتطلب مراجعة قانونية / تهيئة** (العنوان المسجل ورقم
السجل التجاري والرقم الضريبي غير مُهيَّأة بعد).

## 2. ماذا تقدم USAM

منصة بحث عن وظائف وتوظيف. تجمع وتتحقق من إعلانات الوظائف، وتتيح لطالبي العمل بناء ملفات شخصية/سير
ذاتية، والتقديم على الوظائف، واستخدام أدوات مدعومة بالذكاء الاصطناعي (راجع [إفصاح استخدام الذكاء
الاصطناعي ورشيد](/legal/ai-disclosure))، والاختيار الطوعي للظهور لأصحاب العمل عبر "قائمة المواهب".

## 3. التقديم المباشر

عندما يُظهر إعلان الوظيفة إجراء "تقديم مباشر"، فإنه يأخذك إلى صفحة التقديم الخاصة بصاحب العمل نفسه أو
نظام تتبع المتقدمين (ATS) — وهو **إعادة توجيه لطرف ثالث**، وليس طلباً يُقدَّم بالنيابة عن USAM.

## 4. الحسابات

يجب تقديم معلومات دقيقة عند إنشاء الحساب. يمكنك حذف حسابك في أي وقت من الإعدادات.

## 5. قائمة المواهب والظهور

الظهور في عمليات بحث أصحاب العمل ("قائمة المواهب") **معطّل افتراضياً** ولا يحدث إلا إذا فعّلته صراحة.

## 6. ميزات الذكاء الاصطناعي

**الذكاء الاصطناعي يساعد، ولا يتخذ قرارات التوظيف النهائية.** راجع [إفصاح استخدام الذكاء الاصطناعي
ورشيد](/legal/ai-disclosure).

## 7. المدفوعات

راجع [سياسة الاسترداد والإلغاء](/legal/refunds) و[سياسة أمان الدفع والبطاقات](/legal/payment-security).
الأسعار تُعرض وتُحصَّل بالجنيه المصري (EGP) افتراضياً إلا إذا نُص على خلاف ذلك.

## 8. الإنهاء

يجوز لنا تعليق أو إنهاء الحسابات التي تخالف هذه الشروط.

## 9. القانون الحاكم

**يتطلب مراجعة قانونية / تهيئة** — لم يُحدَّد القانون الحاكم وآلية حل النزاعات بعد.

## 10. تغييرات هذه الشروط

نُصدر إصدارات مُرقَّمة لكل تغيير جوهري، وتتطلب إعادة موافقتك قبل الاستمرار في استخدام المنصة.
""",
    "privacy": """# سياسة الخصوصية

**الحالة: مسودة — تتطلب مراجعة قانونية / تهيئة. ترجمة آلية غير مراجعة.**

توضّح هذه السياسة ما تجمعه USAM Career فعلياً من بيانات شخصية وكيف تُستخدم، بناءً على كيفية بناء
المنصة اليوم. لا نزعم الالتزام الكامل بأي إطار تنظيمي محدد؛ وحين لا تكون حقيقة قانونية مؤكدة بعد،
نذكر ذلك صراحةً بدلاً من التخمين.

## 1. من يعالج بياناتك

**يتطلب مراجعة قانونية / تهيئة** لاسم الكيان المسؤول عن المعالجة وتفاصيل الاتصال به.

## 2. ما نجمعه

بيانات الحساب، بيانات الملف الشخصي والسيرة الذاتية، بيانات التقديم، بيانات قائمة المواهب (فقط عند
الاختيار الطوعي)، بيانات تمارين المقابلات (يُحذف التسجيل الصوتي بعد تحويله إلى نص، ويُحتفظ بالنص)،
بيانات الدفع (**لا نستقبل أو نخزّن أبداً رقم البطاقة أو رمز التحقق CVV** — راجع [سياسة أمان الدفع
والبطاقات](/legal/payment-security))، ملفات تعريف الارتباط، وبيانات الاستخدام.

## 3. ما لا نقوم به حالياً

لا نستخدم أدوات تتبع تحليلات أو إعلانات من طرف ثالث. لا نبيع بياناتك الشخصية لأي طرف ثالث. لا نستخدم
الذكاء الاصطناعي لاتخاذ قرار توظيف نهائي.

## 4. حقوقك

راجع [مركز الخصوصية](/app/privacy-center) لممارسة حقوقك في الوصول والتصحيح والحذف والتقييد والتصدير
والاعتراض وسحب الموافقة.

## 5. قائمة المواهب وظهورك لأصحاب العمل

ملفك **غير مرئي لأصحاب العمل افتراضياً**. يتطلب التفعيل الصريح من الإعدادات.

## 6. الاحتفاظ بالبيانات

عدة فئات (مثل نصوص المقابلات) لا تملك فترة احتفاظ مؤكدة قانونياً بعد، وتبقى موسومة "تتطلب مراجعة
قانونية" حتى تُحدَّد.

## 7. النقل الدولي للبيانات

**يتطلب مراجعة قانونية / تهيئة.**

## 8. بيانات الأطفال

**يتطلب مراجعة قانونية / تهيئة.** لا يوجد حد سن أدنى مؤكد قانونياً بعد.

## 9. التواصل

استخدم [مركز الخصوصية](/app/privacy-center) لتقديم طلب بيانات.
""",
    "cookies": """# سياسة ملفات تعريف الارتباط

**ترجمة آلية غير مراجعة.**

نستخدم عدداً محدوداً من ملفات تعريف الارتباط وبيانات التخزين المحلي لتشغيل المنصة. عند زيارتك الأولى
يمكنك اختيار **قبول الكل** أو **رفض غير الضروري** أو **إدارة التفضيلات**. يمكنك تغيير اختيارك في أي
وقت من رابط إعدادات ملفات تعريف الارتباط في التذييل. **ملفات تعريف الارتباط الضرورية لا تُقيَّد
بالموافقة أبداً ولا تعيق تسجيل الدخول.**

## الفئات

- **ضرورية بشكل صارم** — إدارة الجلسة والأمان وحالة تسجيل الدخول. مفعّلة دائماً.
- **وظيفية** — تتذكر التفضيلات مثل اللغة والمظهر.
- **تحليلية** — **غير مستخدمة حالياً** على هذه المنصة (مؤكد بمراجعة الكود).
- **تسويقية** — **غير مستخدمة حالياً.**

## ما نخزّنه فعلياً اليوم

رموز المصادقة الحالية تُخزَّن في `localStorage` للمتصفح، لا في ملفات تعريف الارتباط — راجع [نظرة عامة
على الأمان](/legal/security).
""",
    "refunds": """# سياسة الاسترداد والإلغاء

**الحالة: مسودة — تتطلب مراجعة قانونية / تهيئة لنافذة الاسترداد والكيان القانوني. ترجمة آلية غير
مراجعة.**

## الاشتراكات

كل عملية شراء على هذه المنصة اليوم هي **رسوم لمرة واحدة** تُفعِّل خطة — لا يوجد تجديد تلقائي متكرر.
لا يوجد شيء "يُلغى" لإيقاف رسوم مستقبلية، لأنه لا توجد رسوم مستقبلية مُجدولة أصلاً من هذه المنصة.

## نافذة الاسترداد

نافذة الاسترداد قابلة للتهيئة من قِبل الإدارة وغير مُحددة بعدد أيام ثابت في هذه السياسة. حتى يؤكدها
المستشار القانوني: **تتطلب مراجعة قانونية / تهيئة — لم تُؤكَّد نافذة استرداد بعد.**

## كيف تُعالَج المبالغ المستردة

تُصدَر المبالغ المستردة المعتمدة عبر مزود الدفع نفسه المستخدم في الرسوم الأصلية وتُسجَّل في سجلنا
المالي كقيد عكسي مرتبط — لا يُعاد كتابة سجل الدفع الأصلي أو حذفه أبداً.

## المدفوعات الفاشلة أو المرفوضة

الدفع الفاشل أو المرفوض لا يمنح أبداً الوصول إلى ميزة مدفوعة.

## لا توجد تجارب أو كوبونات مُفترَضة

لا نُعلن عن تجارب مجانية أو كوبونات خصم في هذه الصفحة إلا إذا كانت مُفعَّلة فعلياً في المنصة.
""",
    "payment-security": """# سياسة أمان الدفع والبطاقات

**ترجمة آلية غير مراجعة.**

تلتزم USAM Career بحماية خصوصية وأمان معلوماتك المالية والشخصية. توضح هذه السياسة كيف نقوم بجمع
واستخدام وحماية بيانات الدفع الخاصة بك عند إجراء المعاملات على موقعنا jobs.usamif.com.

## ما لا نقوم به أبداً

**لا تستقبل USAM أو تُرسل أو تُخزّن أبداً رقم بطاقتك الكامل (PAN)، أو رمز التحقق CVV/CVC، أو بيانات
الشريط المغناطيسي، أو الرقم السري (PIN).** هذه قاعدة بنيوية صارمة، لا مجرد وعد في سياسة — مؤكدة بمراجعة
الكود: لا يوجد حقل في أنظمتنا يحمل اسم أو يخزّن رقم بطاقة أو CVV، وكل عمليات الدفع الحالية تُحوَّل إلى
صفحة دفع مُستضافة من مزود الدفع نفسه.

## كيف يعمل الدفع فعلياً اليوم

- تكامل الدفع النشط (Stripe) يستخدم **صفحة دفع مُستضافة من المزوّد** — تُدخل تفاصيل بطاقتك مباشرة على
  صفحة المزوّد، لا على نموذج تتحكم به USAM.
- تكامل ثانٍ (AlexBank) موجود في الكود لكنه **غير مُفعَّل** — وهو هيكل أولي يرفض عمداً معالجة أي دفعة
  حقيقية.

## أمان الإشعارات الفورية (Webhook)

تتغير حالة الدفع فقط بعد التحقق من التوقيع المشفر الخاص بالمزوّد — لا نُحدِّث حالة اشتراكك أو طلبك
لمجرد أن المتصفح أبلغنا بنجاح الدفع.

## المصادقة الثلاثية (3D Secure)

عند الحاجة، تُدار المصادقة الإضافية بالكامل من خلال تدفق المزوّد المُستضاف.

## نطاق معيار أمان بيانات بطاقات الدفع (PCI DSS)

بما أن بيانات البطاقة لا تلمس خوادم USAM أبداً، فإن نطاق تعرضنا لمعيار PCI DSS مُخفَّض بشكل كبير.
**لا نزعم أي شهادة أو مستوى التزام بـ PCI DSS** — يتطلب ذلك تقييماً من جهة مؤهلة لم يحدث بعد.

## لا شعارات أمان مُزيَّفة

لا نعرض شعارات أو شهادات أمان دفع على هذه المنصة إلا إذا كانت حقيقية وقابلة للتحقق.
""",
    "security": """# نظرة عامة على الأمان

**ترجمة آلية غير مراجعة.** تصف هذه الصفحة ممارسات أمنية حقيقية وقابلة للتحقق — لا عبارات تسويقية.

## المصادقة

- كلمات المرور مُجزَّأة (لا تُخزَّن كنص صريح أبداً). رموز الجلسة قصيرة العمر (JWT) مع تدوير تلقائي.
- **ثغرة معروفة (قيد المعالجة):** رموز الوصول/التحديث تُخزَّن حالياً في `localStorage` للمتصفح، وهو
  أكثر عرضة لهجمات XSS من جلسة تعتمد على ملف تعريف ارتباط httpOnly.

## أمان الملفات

- جميع ملفات السيرة الذاتية ووثائق إثبات ملكية الشركة يتم فحصها من حيث النوع والحجم ومحاكاة نوع
  المحتوى، وفحصها بحثاً عن البرمجيات الخبيثة قبل قبولها.
- عند عرض صاحب العمل لسيرة ذاتية متقدم، يتم التحقق من الصلاحية في كل مرة.
- **ثغرة معروفة (قيد المعالجة):** التخزين الأساسي للملفات لا يعتمد بعد على روابط مُوقَّعة ومحدودة
  الصلاحية.

## المدفوعات

راجع [سياسة أمان الدفع والبطاقات](/legal/payment-security).

## الإبلاغ عن مشكلة أمنية

**يتطلب مراجعة قانونية / تهيئة** — لم يُحدَّد عنوان اتصال أمني مخصص بعد.
""",
    "ai-disclosure": """# إفصاح استخدام الذكاء الاصطناعي ورشيد

**ترجمة آلية غير مراجعة.** تستخدم USAM نماذج ذكاء اصطناعي في عدة ميزات. تسرد هذه الصفحة ذلك بصدق.

## رشيد (مساعد المسار المهني بالذكاء الاصطناعي)

يُجيب رشيد على أسئلة المسار المهني ويساعد في السيرة الذاتية. **لا يتخذ قرارات توظيف وليس له أي سلطة
على خيارات أي صاحب عمل.**

## مطابقة الوظائف والتوصيات

محرك المطابقة يُرتِّب الوظائف بناءً على ملفك الشخصي. **هذه أداة ترتيب/اقتراح، لا قرار توظيف.**

## تمارين المقابلات (صوت/نص)

عند استخدام تمارين المقابلة الصوتية، يُحوَّل صوتك إلى نص ثم يُحذف الملف الصوتي الأصلي.

## ما لا يفعله الذكاء الاصطناعي هنا

**لا يتخذ الذكاء الاصطناعي القرار النهائي بتوظيف أو رفض أو تقديم عرض لأي متقدم على هذه المنصة.**
""",
    "acceptable-use": """# سياسة الاستخدام المقبول

**ترجمة آلية غير مراجعة.** توضح هذه الصفحة ما لا يجوز لك فعله على USAM Career، بشكل منفصل عن [شروط
الخدمة](/legal/terms) العامة.

## الاستخدامات المحظورة

كشط البيانات أو تنزيلها بشكل جماعي، إنشاء حسابات أو وظائف أو طلبات تقديم مزيفة، رفع برمجيات خبيثة أو
ملفات مصممة لاستغلال ثغرات، تجاوز إعداد ظهور قائمة المواهب لمستخدم آخر، التدخل في آلية **التحقق من
التقديم المباشر**.

## التحقق من التقديم المباشر — قاعدة مُطبَّقة فعلياً في الكود

نظام استيراد الوظائف في USAM مُصمَّم لرفض روابط التقديم التي تمر عبر وسيط تجميع من طرف ثالث بدلاً من
موقع صاحب العمل أو نظام تتبع المتقدمين الخاص به — يتم تطبيق هذا في الكود عند الاستيراد، وليس مجرد نص
في سياسة.

## سلوك أصحاب العمل

يجوز لأصحاب العمل البحث عن أو التواصل فقط مع المتقدمين الذين اختاروا الظهور في قائمة المواهب.

## التطبيق

يجوز لنا تعليق أو إنهاء حساب يخالف هذه السياسة.
""",
    "data-rights": """# حقوقك في البيانات

**ترجمة آلية غير مراجعة.** تشرح هذه الصفحة حقوقك في بياناتك الشخصية على USAM Career.

## ما يمكنك فعله اليوم مباشرة

من [مركز الخصوصية](/app/privacy-center): **الوصول** لطلب تصدير بياناتك، **التصحيح** في الإعدادات،
**الحذف** مع فترة سماح 30 يوماً قابلة للإلغاء، **سحب الموافقة** لقائمة المواهب أو التسويق، **الاعتراض**
عبر طلب رسمي (DSR) يُتابَع حتى حالة نهائية.

## تتبع حالة الطلب

كل طلب DSR يُظهر سجل أحداث حقيقي ومُتراكم.

## ما لا تفعله هذه الصفحة

لا تزعم حقاً لا ينطبق على نطاقك القضائي (مثل قابلية نقل البيانات)، ولا تَعِد بمدة استجابة لا يمكن
لهذا الكود الالتزام بها فعلياً. **يتطلب مراجعة قانونية / تهيئة** لمدة الاستجابة الدقيقة المعروضة لك.
""",
    "subprocessors": """# إفصاح معالجي البيانات الفرعيين

**ترجمة آلية غير مراجعة.** معالج البيانات الفرعي هو مزوّد يعالج بيانات شخصية بالنيابة عن USAM Career.

## المعالجون الفرعيون الحاليون

**Amazon Web Services (AWS)** — بنية تحتية سحابية واستضافة نماذج الذكاء الاصطناعي. **Stripe, Inc.** —
مزوّد الدفع المُستضاف النشط. **Typesense** — فهرسة البحث (مُستضافة ذاتياً افتراضياً). **Sentry** —
تتبع أخطاء الخادم فقط.

## ما لا تزعمه هذه الصفحة

**حالة اتفاقية معالجة البيانات (DPA) لكل مزوّد موسومة "غير مؤكدة بعد"** بدلاً من افتراض توقيعها.

## ملاحظة مسار نموذج الذكاء الاصطناعي

يعمل رشيد عبر AWS Bedrock الذي يستضيف النموذج الأساسي. مزوّد النموذج (مثل Anthropic) هو **مسار
استضافة نموذج يتم الوصول إليه بالكامل عبر حدود بنية AWS التحتية**، لا معالج فرعي مستقل تتعاقد معه
USAM مباشرة.
""",
    "international-transfers": """# النقل الدولي للبيانات

**ترجمة آلية غير مراجعة.** توضح هذه الصفحة بصدق ما نعرفه وما لا نعرفه بعد عن النقل العابر للحدود.

## ما يمكن تأكيده اليوم

قد تُعالج أو تُخزَّن بياناتك في مناطق خارج مصر والسعودية حسب تهيئة كل خدمة. نحتفظ بسجل داخلي للنقل
العابر للحدود يتتبع دولة الوجهة وفئات البيانات والآلية القانونية المُعتمد عليها.

## ما يتطلب مراجعة قانونية / تهيئة

**لا يوجد في سجلنا أي نقل له آلية ضمان أو مرجع تفويض قانوني مؤكد حالياً.** قانون حماية البيانات
المصري يتطلب تفويضاً مسبقاً من المركز القومي لحماية البيانات **بالإضافة إلى** موافقة صريحة من صاحب
البيانات لكل عملية نقل. نظام حماية البيانات السعودي يتطلب آلية ضمان معتمدة (بنود تعاقدية نموذجية،
قواعد ملزمة مشتركة، شهادة، أو موافقة لكل حالة).
""",
    "candidate-privacy": """# إشعار خصوصية المتقدمين للوظائف

**ترجمة آلية غير مراجعة.** هذا الإشعار مُخصَّص لطالبي العمل المتقدمين لوظيفة على USAM Career — يُعرض
عند التقديم، لا فقط داخل [سياسة الخصوصية](/legal/privacy) العامة.

## ماذا يحدث عند التقديم

يُشارَك طلبك (بيانات الملف الشخصي والسيرة الذاتية وأي إجابات نموذج مخصص) مع **صاحب العمل المحدد فقط**
— لا يُضاف تلقائياً إلى قائمة المواهب العامة. إذا كان الإعلان "تقديم مباشر"، فإنك تُحوَّل إلى موقع
صاحب العمل أو نظام تتبع المتقدمين الخاص به.

## قائمة المواهب منفصلة عن التقديم

التقديم على وظيفة محددة **ليس** نفس الشيء كالاشتراك في قائمة المواهب — يبقى الظهور معطّلاً حتى تُفعِّله
صراحة.

## دور الذكاء الاصطناعي في طلبك

إذا شاركت ميزات المطابقة في عرض هذا الإعلان لك، **فإن صاحب العمل، وهو إنسان، يتخذ قرار التوظيف
الفعلي.**

## حقوقك في هذه البيانات

راجع [حقوقك في البيانات](/legal/data-rights) و[مركز الخصوصية](/app/privacy-center).
""",
    "business-terms": """# شروط أصحاب العمل والشركات

**ترجمة آلية غير مراجعة.** تنطبق هذه الشروط على حسابات أصحاب العمل/الشركات، بالإضافة إلى [شروط
الخدمة](/legal/terms) العامة.

## ما يمكن لحساب صاحب العمل فعله

نشر إعلانات وظائف، البحث عن المتقدمين الذين اختاروا الظهور في قائمة المواهب فقط، عرض وإدارة الطلبات
المُقدَّمة لإعلاناته الخاصة فقط (مع تحقق صلاحية في كل طلب)، إدارة فريق مستخدمين تحت حساب الشركة نفسه.

## التحقق

تُفحص إعلانات الوظائف وروابط التقديم المباشر المرتبطة بها مقابل نطاق صاحب العمل عند الإمكان.

## الفوترة

تُشترى خطط أصحاب العمل بنفس طريقة الخطط الفردية: رسوم لمرة واحدة بدون تجديد تلقائي.

## التزامات بيانات المتقدمين

يجب على صاحب الحساب التعامل مع بيانات المتقدمين بما يتوافق مع قانون حماية البيانات المعمول به، وعدم
إعادة توزيعها لطرف ثالث خارج نطاق تقييم ذلك المتقدم للدور الذي قدّم عليه.

## الإنهاء

يجوز لنا تعليق أو إنهاء حساب صاحب عمل يخالف هذه السياسة.
""",
}


class Command(BaseCommand):
    help = (
        "Seed baseline Legal/Privacy domain data (policy DOCUMENTS as DRAFT "
        "versions, consent purposes, cookie categories, jurisdictions, "
        "processors). Does NOT publish anything by default — policy "
        "versions are created as DRAFT and must be explicitly reviewed, "
        "approved, and activated via the Admin Legal Control Plane before "
        "they appear on any public /legal/<slug> route."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--activate-drafts", action="store_true",
            help=(
                "TEST/STAGING CONVENIENCE ONLY — immediately approve+activate "
                "the seeded draft versions so /legal/<slug> is populated "
                "without a manual review step. Never use this in a "
                "production deploy; the default (omitting this flag) is the "
                "safe, directive-mandated behavior. Refused outright unless "
                "settings.DEBUG=True or LEGAL_SEED_ALLOW_ACTIVATE_DRAFTS is "
                "explicitly set — see the same guard pattern already used "
                "by AlexBankMockProvider."
            ),
        )

    def handle(self, *args, **options):
        activate = options["activate_drafts"]
        if activate:
            self._guard_activate_drafts_not_production()
        self._seed_documents(activate=activate)
        self._seed_consent_purposes()
        self._seed_cookie_categories()
        self._seed_jurisdictions()
        self._seed_ai_disclosures()
        self._seed_retention_matrix()
        self._seed_processors()
        LegalEntityConfig.load()  # ensure the singleton row exists, unconfigured
        if activate:
            self.stdout.write(self.style.WARNING(
                "Legal domain seed complete — drafts were AUTO-ACTIVATED "
                "(--activate-drafts). Do not use this flag in production."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Legal domain seed complete. Policy versions are DRAFT and "
                "NOT yet public. Review and activate via the Admin Legal "
                "Control Plane before launch. Run `manage.py legal_readiness` "
                "to check overall launch readiness."
            ))

    def _guard_activate_drafts_not_production(self):
        """Refuse `--activate-drafts` unless this is clearly a non-production
        environment. Mirrors the existing `AlexBankMockProvider._guard()`
        pattern (apps.payments.providers.alexbank_provider) rather than
        inventing a new convention: a command that can auto-publish
        machine-translated/unreviewed legal text is exactly as dangerous as
        a payment provider that can fake a live charge, and this platform
        already has one correct answer for that shape of risk.

        Allowed when EITHER:
          - settings.DEBUG is True (the standard dev/test signal this repo
            already uses everywhere, e.g. config/settings/test.py,
            development.py), OR
          - LEGAL_SEED_ALLOW_ACTIVATE_DRAFTS is explicitly set in the
            environment (an escape hatch for a deliberately-configured
            staging box that runs with DEBUG=False but still wants this
            convenience — requires an explicit opt-in, never a default).

        Raises CommandError (not a silent no-op) so a CI/deploy script that
        accidentally includes this flag fails loudly instead of partially
        succeeding.
        """
        from django.conf import settings
        from django.core.management.base import CommandError
        from decouple import config as _config

        allow = bool(getattr(settings, "DEBUG", False)) or _config(
            "LEGAL_SEED_ALLOW_ACTIVATE_DRAFTS", default=False, cast=bool,
        )
        if not allow:
            raise CommandError(
                "--activate-drafts is refused: settings.DEBUG is False and "
                "LEGAL_SEED_ALLOW_ACTIVATE_DRAFTS is not set. This flag "
                "auto-publishes machine-translated/unreviewed legal text "
                "and must never run against a production database. If this "
                "really is a deliberately-configured staging environment, "
                "set LEGAL_SEED_ALLOW_ACTIVATE_DRAFTS=1 explicitly."
            )

    def _seed_documents(self, activate: bool = False):
        """Create PolicyDocuments + an initial v2026.1 version for each.

        Directive-mandated: seeding must NEVER silently publish unreviewed
        legal text. The default behavior creates the version as DRAFT only —
        it is NOT visible on any public `/legal/<slug>` route until an admin
        explicitly runs it through DRAFT -> IN_REVIEW -> APPROVED -> ACTIVE
        (via the Admin Legal Control Plane or `services.activate_version`).

        `activate=True` exists ONLY for test/staging convenience (e.g. the
        local dev environment, or a CI fixture) — it is never the default
        and is gated behind an explicit `--activate-drafts` CLI flag so a
        production deploy can never accidentally pass it by habit.

        Re-running this command is always safe: if a document already has
        ANY version (DRAFT or ACTIVE), nothing is touched — an existing
        ACTIVE production policy is never replaced or retired by seeding.
        """
        docs = [
            ("terms", PolicyDocument.DocType.TERMS, "Terms of Service", TERMS_MD),
            ("privacy", PolicyDocument.DocType.PRIVACY, "Privacy Policy", PRIVACY_MD),
            ("cookies", PolicyDocument.DocType.COOKIES, "Cookie Policy", COOKIES_MD),
            ("refunds", PolicyDocument.DocType.REFUNDS, "Refund & Cancellation Policy", REFUNDS_MD),
            ("payment-security", PolicyDocument.DocType.PAYMENT_SECURITY, "Payment & Card Security Policy", PAYMENT_SECURITY_MD),
            ("security", PolicyDocument.DocType.SECURITY, "Security Overview", SECURITY_MD),
            ("ai-disclosure", PolicyDocument.DocType.AI_DISCLOSURE, "AI Use & Rasheed Disclosure", AI_DISCLOSURE_MD),
            # Added 2026-09-21 continuation pass — see module docstring above.
            ("acceptable-use", PolicyDocument.DocType.ACCEPTABLE_USE, "Acceptable Use Policy", ACCEPTABLE_USE_MD),
            ("data-rights", PolicyDocument.DocType.DATA_RIGHTS, "Your Data Rights", DATA_RIGHTS_MD),
            ("subprocessors", PolicyDocument.DocType.SUBPROCESSORS, "Sub-processor Disclosure", SUBPROCESSORS_MD),
            ("international-transfers", PolicyDocument.DocType.INTERNATIONAL_TRANSFERS,
             "International Data Transfers", INTERNATIONAL_TRANSFERS_MD),
            ("candidate-privacy", PolicyDocument.DocType.CANDIDATE_PRIVACY, "Candidate Privacy Notice", CANDIDATE_PRIVACY_MD),
            ("business-terms", PolicyDocument.DocType.BUSINESS_TERMS, "Employer & Business Terms", BUSINESS_TERMS_MD),
        ]
        for slug, doc_type, title, content in docs:
            doc, _ = PolicyDocument.objects.get_or_create(
                slug=slug, defaults={"doc_type": doc_type, "title": title},
            )
            if doc.versions.filter(locale="en").exists():
                # An ACTIVE (or even just DRAFT) version already exists —
                # never silently replace/duplicate it. This is what makes
                # re-running the command safe against a live production
                # policy that an admin already reviewed and activated.
                self.stdout.write(f"Skip (already versioned): {slug} (en)")
            else:
                version = PolicyVersion.objects.create(
                    document=doc, version_label="2026.1", locale="en",
                    jurisdiction="OTHER", status=PolicyVersion.Status.DRAFT,
                    content_markdown=content,
                    summary_of_changes="Initial draft seeded pending legal review.",
                )
                if activate:
                    # Test/staging convenience path ONLY — never the
                    # production default. Still goes through the real
                    # APPROVED gate inside activate_version (DRAFT cannot
                    # jump straight to ACTIVE).
                    version.status = PolicyVersion.Status.APPROVED
                    version.save(update_fields=["status"])
                    # This seeded placeholder content still contains
                    # unresolved "REQUIRES LEGAL REVIEW" markers (legal
                    # entity, refund window, etc. aren't configured yet) —
                    # allow_unresolved_markers is required here ONLY
                    # because --activate-drafts is an explicit test/staging
                    # convenience flag, never reachable from the Admin
                    # Legal Control Plane or any production path.
                    services.activate_version(version=version, allow_unresolved_markers=True)
                    self.stdout.write(f"Created + activated (--activate-drafts): {slug} v2026.1 (en)")
                else:
                    self.stdout.write(
                        f"Created DRAFT (not public yet): {slug} v2026.1 (en) — "
                        f"review and activate via Admin Legal Control Plane."
                    )

            # Arabic locale — unreviewed machine translation, explicitly
            # flagged via is_machine_translated=True (never silently
            # presented as an official equivalent). Seeded as its own
            # independent DRAFT row (same unique constraint as the English
            # row: document + version_label + locale), so activating or
            # editing one locale never touches the other.
            ar_content = AR_TRANSLATIONS.get(slug)
            if ar_content and not doc.versions.filter(locale="ar").exists():
                ar_version = PolicyVersion.objects.create(
                    document=doc, version_label="2026.1", locale="ar",
                    jurisdiction="OTHER", status=PolicyVersion.Status.DRAFT,
                    content_markdown=ar_content, is_machine_translated=True,
                    summary_of_changes="Initial draft (unreviewed machine translation) seeded pending legal + translation review.",
                )
                if activate:
                    ar_version.status = PolicyVersion.Status.APPROVED
                    ar_version.save(update_fields=["status"])
                    services.activate_version(version=ar_version, allow_unresolved_markers=True)
                    self.stdout.write(f"Created + activated (--activate-drafts): {slug} v2026.1 (ar)")
                else:
                    self.stdout.write(f"Created DRAFT (not public yet): {slug} v2026.1 (ar)")

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

        Directive item 21 correction: entries are now tagged with a
        `processor_type` note distinguishing three DIFFERENT kinds of thing
        this register was previously flattening together:
          - "external_processor": a genuinely separate legal entity that
            receives/processes personal data on USAM's behalf under its own
            terms (Stripe, Sentry).
          - "cloud_infrastructure": AWS itself, as the underlying compute/
            storage substrate — a processor in the GDPR sense, but a single
            infrastructure vendor, not many.
          - "model_path_via_infrastructure": AI inference that runs ON AWS
            Bedrock as a hosted model-serving path (confirmed in code:
            apps/intelligence/bedrock_plugin.py calls Bedrock's
            InvokeModel API against Anthropic Claude model IDs like
            "us.anthropic.claude-...") — Anthropic is NOT a direct
            processor here: USAM's data never leaves AWS's boundary to
            reach Anthropic as a separate API counterparty. The register
            previously had no way to express this distinction and risked
            implying "Anthropic" should be listed as its own separate
            processor, which would overstate the real data flow.
        Typesense's deployment mode (self-hosted vs. Typesense Cloud) is a
        genuine fork in whether it's even a processor at all — self-hosted
        Typesense never receives data outside USAM's own infrastructure, so
        it is only a true third-party processor when TYPESENSE_HOST points
        at a Typesense Cloud instance rather than a self-managed container
        (confirmed: docker-compose.yml provisions a self-hosted `typesense`
        service by default for this platform).
        """
        processors = [
            dict(
                name="Amazon Web Services (AWS)",
                purpose="Cloud infrastructure AND AI model-hosting substrate: S3 "
                        "(CV/media/interview-audio storage), Bedrock (hosted AI model "
                        "inference — see note below on what this actually means for "
                        "Anthropic), Transcribe + Polly (voice interview speech-to-text/"
                        "text-to-speech), Secrets Manager (credential storage).",
                data_categories="CV/resume files, interview audio (deleted post-transcription), "
                                "AI prompt/response content, encrypted secrets",
                country="Varies by configured AWS region",
                notes="processor_type=cloud_infrastructure. This is the ONE real "
                      "infrastructure processor for all AWS-hosted services below — "
                      "not a stand-in for every AI model accessible through Bedrock.",
            ),
            dict(
                name="Anthropic (Claude models, via AWS Bedrock — NOT a direct API relationship)",
                purpose="AI model path, not a separate processor: Rasheed/matching/CV-parsing "
                        "features call AWS Bedrock's InvokeModel API against Anthropic Claude "
                        "model IDs (confirmed in code: apps/intelligence/bedrock_plugin.py, "
                        "model IDs such as 'us.anthropic.claude-sonnet-...'). Bedrock is a "
                        "hosted model-serving layer run entirely within AWS's infrastructure — "
                        "USAM has no direct API key, account, or contract with Anthropic, and "
                        "prompt/response data does not leave AWS's boundary to reach Anthropic "
                        "as an independent counterparty.",
                data_categories="AI prompt/response content (same data AWS already processes "
                                "as the hosting infrastructure — not an additional data flow)",
                country="N/A — routed entirely through AWS Bedrock's infrastructure",
                notes="processor_type=model_path_via_infrastructure. Listed here for "
                      "transparency about WHICH underlying model family is used, not because "
                      "Anthropic is a separate contracted processor. dpa_signed intentionally "
                      "left NULL — there is no direct USAM-Anthropic DPA to confirm or deny.",
            ),
            dict(
                name="Stripe, Inc.",
                purpose="Payment processing via Stripe-hosted Checkout. Card data is "
                        "entered directly on Stripe's hosted page and never transits USAM's "
                        "servers.",
                data_categories="Order/payment metadata (amount, currency, reference) — "
                                "no card/PAN/CVV data",
                country="United States (Stripe's registered jurisdiction)",
                notes="processor_type=external_processor — a genuine separate legal entity "
                      "receiving data under its own terms.",
            ),
            dict(
                name="Typesense",
                purpose="Full-text/faceted job search index. Deployed self-hosted by default "
                        "for this platform (docker-compose.yml provisions a self-managed "
                        "Typesense container) — in that mode it runs entirely within USAM's "
                        "own infrastructure and is NOT a third-party data processor. It only "
                        "becomes a genuine external processor if a deployment is instead "
                        "pointed at a Typesense Cloud-hosted instance.",
                data_categories="Job listing content (titles, descriptions, company names) — "
                                "not personal/candidate data",
                country="Depends on deployment (self-hosted vs. Typesense Cloud region)",
                notes="processor_type=self_hosted_infrastructure (default) OR "
                      "external_processor (ONLY if configured against Typesense Cloud — "
                      "confirm actual deployment mode before treating this as a third party).",
            ),
            dict(
                name="Sentry",
                purpose="Backend error tracking and performance monitoring "
                        "(sentry-sdk, server-side only — not a browser-loaded tracker).",
                data_categories="Error stack traces, request metadata; PII scrubbing "
                                "behavior depends on Sentry project configuration",
                country="Depends on configured Sentry region/plan",
                notes="processor_type=external_processor — a genuine separate legal entity "
                      "receiving data under its own terms.",
            ),
        ]
        for data in processors:
            ProcessorRecord.objects.get_or_create(name=data["name"], defaults=data)
        self.stdout.write(
            "Processor register seeded (AWS, Stripe, Typesense, Sentry — confirmed by code). "
            "contract_reference/dpa_signed left unset for legal to confirm."
        )
        self.stdout.write("Retention matrix seeded.")
