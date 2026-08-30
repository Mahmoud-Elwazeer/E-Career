# PROMPT — E-Career: FINAL Platform Completion Pass (everything remaining, in one place)

You are a senior full-stack engineer + release manager doing the FINAL
completion pass on E-Career at `M:\job already web for jobs\E-Career`
(Django/DRF backend in `backend/`, React/Vite frontend in `frontend/`,
Chrome extension POC in `browser-extension/`). Read `AGENTS.md`,
`CLAUDE.md`, and — in order — every completion report in `audit/`
(`PHASE_0` through `PHASE_7C_COMPLETION_REPORT.md`,
`DEEP_CHECK_AND_PUSH_REPORT.md`, `LIVE_VERIFICATION_REPORT.md`) before
touching anything. This repo has a long, well-documented history of
status docs overclaiming completeness — spot-check at least 3 claims per
report against actual current code before trusting any of it, same
discipline every prior phase used.

## Where the project actually stands (verified, not assumed, as of this prompt)

- Phases 0-3 (66 items), Phase 4 (67 test failures), a Deep-Check pass,
  a Live Verification pass (11 engines, real HTTP), Phase 5 (6
  Jobright-style features), Phase 6 (GitHub-vs-local reconciliation + 5
  real bugs found/fixed), and Phase 7a/7b/7c (admin control plane
  consolidation, AI copilot, entitlements, AI cost tracking fixes,
  global search, Celery Beat viewer, GDPR tooling, and — critically — a
  fix confirmed via direct inspection that `pydantic_ai` is now actually
  installed and the live Rashid chat path now actually calls the real
  tool-calling agent, not a dead-code path) are all complete and
  committed locally on `development`.
- Backend test suite, TypeScript compile, and production build were all
  green as of the last report.
- **The only remaining items are the ones that were EXPLICITLY deferred
  across every phase report, for real reasons (human-action-only, or a
  deliberate business-decision gate) — not oversights.** This prompt's
  job is to close every one of them that CAN be closed in code, and give
  you a definitive, final list of what genuinely cannot (because it
  requires the platform owner's direct action in an external console/
  account, not a code change).

## Part 1 — Code-closable remaining items (do these)

1. **Chrome extension coverage**: `browser-extension/` is still a
   single-ATS POC (Greenhouse only, per the Phase 5 report). Extend
   `content-greenhouse.js`'s pattern to at least 2 more of the ATS
   providers named in the original scope (Lever, Ashby are the next-
   easiest — both have simpler, more uniform DOM structures than
   Workday). Each new content script: detect the ATS's form fields,
   fill from the authenticated extension-token profile, NEVER auto-
   submit (same hard rule as every prior phase — a visible "Review &
   submit manually" banner is mandatory). Add a test plan document (not
   automated tests — a browser extension needs manual QA) describing
   exactly how to load-test each ATS's autofill by hand in
   `chrome://extensions` developer mode.
2. **Quick-Apply real ATS submission investigation**: Phase 5's
   `quick_apply_service.py` explicitly stated Greenhouse/Lever/Ashby
   public APIs require employer-specific board tokens E-Career doesn't
   have. Re-verify this is still true (ATS providers occasionally open
   up self-serve API access) — if any provider now offers a self-serve
   path to register your own board-token-free integration, document it
   as a path to real Quick-Apply submission; if not (most likely),
   explicitly confirm the current "prepare + record click-through, human
   submits" design remains the correct, final approach — don't leave
   this as an open question forever.
3. **Analytics/decision-support final layer**: confirm every item in the
   original owner's §19 (analytics: users/jobs/companies/talent/AI/
   business metrics) and §22 (decision-support alerts: scraper failing,
   AI cost spike, recommendation quality drop, queue backlog, security
   event, model failure) has a real, working surface in the admin SPA —
   cross-check against `PHASE_7A/7B/7C_COMPLETION_REPORT.md`'s actual
   endpoint inventories (not the original prompt's wishlist) and build
   ONLY the alerts/metrics that are still missing after everything
   already shipped. Most of §19/§22 should already be covered by
   `AICostDashboardView`, `SystemHealthView`, `ScraperDashboardView`,
   and the existing `AnalyticsTab` — verify before building anything new.
4. **Dependency sanity sweep**: run `pip check` (already confirmed clean
   as of this prompt — re-confirm after any new deps you add) and
   `npm audit` (frontend) — fix any HIGH/CRITICAL vulnerabilities found
   that have a safe non-breaking upgrade path; document (don't silently
   upgrade) anything that would require a breaking major-version bump.
5. **Full final live end-to-end re-verification**: re-run the exact
   11-engine live HTTP check from `audit/prompts/LIVE_VERIFICATION_PROMPT.md`
   one more time, end to end, on a fresh local dev environment (same
   scratch-settings/sqlite/JWT pattern every prior pass used, cleaned up
   afterward) — this is the FINAL confirmation, not a repeat for its own
   sake: confirm Rashid AI (engine 8) now genuinely improves given the
   Phase 7c agent-wiring fix (it may still be blocked by AWS Bedrock
   model access — see Part 2 item 1 — but the AGENT ITSELF calling tools
   correctly should now be verifiable even if the underlying model call
   fails, by checking that the correct tool was attempted).
6. **Documentation cleanup**: this repo has ~100+ historical planning
   `.md` files at the root (`ADVANCED_FEATURES_ROADMAP.md`,
   `CLINE_IMPLEMENTATION_PLAN.md`, `COMPLETE_FEATURE_STATUS_REPORT.md`,
   etc. — confirmed present via `ls *.md` at repo root) that predate this
   entire audit/phase effort and are now stale/contradictory per
   `AGENTS.md`'s own warning. Move them into an `archive/` subdirectory
   (do NOT delete — just get them out of the root so they stop being
   mistaken for current status) and add a one-line pointer at the top of
   each moved file: "Superseded by MASTER_IMPLEMENTATION_PLAN.md and
   audit/PHASE_*_COMPLETION_REPORT.md — kept for history only." Update
   `AGENTS.md` itself if it references any of the old root-level docs by
   path.

## Part 2 — Human-only action items (cannot be closed in code; produce a final, definitive checklist)

Consolidate every human action item repeated across every phase report
into ONE final checklist in your output report, each with the EXACT
action needed (not a vague restatement) and where to do it:

1. **AWS Bedrock model access**: request/confirm access to
   `anthropic.claude-sonnet-4-5-20250929-v1:0` (and its cross-region
   inference profile `us.anthropic.claude-sonnet-4-5-20250929-v1:0`) in
   the AWS Bedrock console → Model access page, for the AWS account this
   deployment uses. This is the single remaining blocker on Rashid AI
   actually generating real responses (the agent-wiring is now fixed per
   Phase 7c; only the underlying model call is blocked).
2. **AWS IAM permissions for voice interviews**: grant the IAM user/role
   this app runs as: `polly:SynthesizeSpeech`, `transcribe:StartStreamTranscription`
   (or the batch equivalent, whichever the code uses — check
   `apps/interviews/voice_service.py`), and S3 read/write on the bucket
   configured via `AWS_STORAGE_BUCKET_NAME`. Also set `AWS_REGION` and
   `AWS_STORAGE_BUCKET_NAME` in the real `.env` if not already set.
3. **`JUDGE0_API_KEY`**: obtain a valid RapidAPI key for Judge0 CE (used
   for coding-interview grading) and set it in `.env`.
4. **AWS access key rotation**: confirm the previously-flagged key
   (`AKIAYK...TGPY`, never actually committed to git per the D9 audit,
   but potentially still live in a local `.env`) has been rotated in the
   AWS IAM console. This has been asked in nearly every phase report —
   get an explicit yes/no from the platform owner and record the answer.
5. **Redis + ClamAV in the real deployment target**: both were worked
   around with LocMemCache/sqlite/skip-scan in every local QA pass — the
   actual production environment needs a real Redis instance (Celery
   broker + django-redis cache + DRF throttle cache) and a real ClamAV
   daemon (CV upload malware scanning, fail-closed by design — uploads
   silently fail if ClamAV is unreachable, which is safe but means CV
   upload is currently non-functional in any environment without it).
6. **Chrome Web Store**: if the extension (Part 1 item 1) is extended and
   the owner wants it distributed, it needs real icon artwork (Phase 6
   already added placeholder PNGs — replace with branded ones), a
   Chrome Web Store developer account, and the standard listing/review
   process — this is a business/ops task, not code.
7. **Phase 8 (Billing)** — remains explicitly deferred
   (`audit/prompts/PHASE_8_BILLING_PROMPT.md`) until the owner makes a
   separate, deliberate decision to monetize. Do not touch it in this
   pass.

## Rules

- Local commits only, do not push — you push via Claude Code in Visual
  Studio yourself.
- Do not weaken `is_discoverable` consent enforcement anywhere.
- No payment/billing code (Part 2 item 7 stays out of scope).
- Real test coverage for every new/changed endpoint with side effects —
  this has been the single most repeated correction across this entire
  project (Phase 5's quick_apply/insider_connections shipped with zero
  tests, caught in Phase 6) — do not let it happen a second time.
- Run the full backend test suite + `npx tsc --noEmit` + `npx vite
  build --mode production` before considering this pass complete.
- Never touch `.env` or read/print any secret.

## When done

Write `audit/FINAL_PLATFORM_COMPLETION_REPORT.md` — the single
consolidated closing document for this entire multi-phase effort:
- Part 1's 6 items: done/partial/deferred with reason, for each.
- Part 2's 7 items: the definitive human-action checklist (exact action
  + exact location), explicitly asking the owner to confirm each one's
  status rather than assuming.
- A final summary table of EVERY phase (0 through 7c) with its
  completion status, item counts, and a link to its own report — the
  single "table of contents" for the whole effort, since ~15 separate
  phase reports now exist in `audit/`.
- End with the same direct, no-hedging verdict every phase has used:
  **"Is E-Career now fully feature-complete and code-ready for
  production deployment, contingent only on the human action items in
  Part 2, or does a genuine code gap remain?"** If a gap remains, name it
  exactly — do not round up to "done" the way this repo's history has
  repeatedly warned against.
