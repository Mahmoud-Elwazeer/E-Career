# PROMPT — E-Career Phase 7c + Critical Finding: pydantic-ai Never Installed, Rashid Agent Never Actually Wired to Live Chat

You are a senior full-stack engineer working on E-Career at
`M:\job already web for jobs\E-Career`. Read `AGENTS.md`, `CLAUDE.md`,
`audit/PHASE_7A_COMPLETION_REPORT.md`, and
`audit/PHASE_7B_COMPLETION_REPORT.md` in full first.

## 🔴 CRITICAL FINDING — verify this yourself before doing anything else

Direct inspection just before writing this prompt found two compounding
problems that predate Phase 7 and were never caught by any prior "Rashid
consolidation" claim:

1. **`pydantic_ai` is not installed in the venv at all** — not a version
   mismatch, not a partial install: `python -c "import pydantic_ai"` →
   `ModuleNotFoundError: No module named 'pydantic_ai'`. `pip show
   pydantic-ai-slim` → "Package(s) not found". This means
   `apps/intelligence/agent.py` (the user-facing Rashid `pydantic-ai`
   agent with tool-calling, including the 3 tools added in Phase 5 —
   `get_match_score`, `tailor_resume`, `find_referral_contacts`) and
   `apps/intelligence/admin_agent.py` (the Phase 7b.1 admin copilot) both
   **cannot import successfully today** and any endpoint that touches
   them will hit an ImportError or the graceful-501 fallback the Phase
   7b report mentions.
2. **The REAL, live Rashid chat path never imports `agent.py` at all.**
   Confirmed via repo-wide grep: `apps/intelligence/agent.py`'s
   `get_rashid_agent`/`create_rashid_agent` functions have exactly ONE
   importer in the entire codebase — `apps/intelligence/views.py` — and
   `apps/rashid/` (the actual app backing the live chat UI, WebSocket
   consumer, and `send_message` action that real users hit) has **zero**
   references to `apps.intelligence.agent` anywhere. Instead,
   `apps/rashid/service.py` calls `career_ai_service.invoke_model()`
   directly (`apps/intelligence/career_ai.py`'s `bedrock_service`) — a
   raw prompt-completion call with NO tool-calling, exactly the
   "prompt concatenation, no real tool-calling" pattern that the
   original D7 audit (`audit/D7_RASHID_AI_INFRA_RESEARCH.md`) flagged as
   the core Rashid architecture problem MONTHS ago.

**Net effect: Phase 5's 3 Rashid tools and Phase 7b's entire Admin AI
Copilot are currently unreachable dead code from any real user or admin
conversation.** The "PARTIAL PASS" verdict on Rashid AI in
`audit/LIVE_VERIFICATION_REPORT.md` undersold this — it attributed the
gap entirely to "AWS Bedrock legacy model access denied," but the tool-
calling agent layer itself was never wired in, independent of the
Bedrock model issue. Fix the Bedrock model access and Rashid chat would
STILL not use any of the pydantic-ai tools, because the live chat path
doesn't call that agent at all.

## Task 1 (do this FIRST, before any Phase 7c polish work)

1. Install `pydantic-ai-slim[bedrock]` (the version already pinned in
   `requirements.txt`, confirmed present there per the Phase 7b report)
   into the venv: `pip install -r requirements.txt` and confirm
   specifically that `python -c "import pydantic_ai; print('ok')"`
   succeeds afterward. If it fails to install cleanly (native deps,
   version conflict, etc.), document the EXACT error — don't silently
   move on.
2. Once installed, actually wire `apps/rashid/service.py`'s live chat
   path to call `get_rashid_agent().run(...)` (or equivalent) INSTEAD of
   `career_ai_service.invoke_model()` directly — this is the real fix,
   not just an import-error fix. Preserve `apps/rashid/service.py`'s
   existing conversation history/persistence logic (don't rebuild
   conversation storage) — only swap the model-invocation call itself to
   go through the tool-calling agent. This is a meaningful, careful
   change to a live user-facing feature: test thoroughly, including a
   real chat message that should trigger one of the Phase 5 tools (e.g.
   ask "what's my match score for job X" and confirm the agent actually
   calls `get_match_score` and returns a real result, not a generic
   text response).
3. Re-test the Admin AI Copilot (Phase 7b.1) end-to-end now that
   `pydantic_ai` is installed — confirm it no longer 501s and its 5
   read-only tools return real data via an actual chat request, not just
   unit-test mocks.
4. Re-run the FULL test suite after this change — this touches a live
   chat path shared by every user, regression risk is real. If ANY test
   that was passing before now fails, do not proceed to Task 2 until it's
   fixed.
5. Write `audit/PHASE_7C_RASHID_AGENT_WIRING_REPORT.md` documenting
   exactly what was broken, what you changed, and live-request evidence
   (not just unit tests) that both the user Rashid chat and the admin
   copilot chat now actually invoke tools and return real tool results.

## Task 2 — Phase 7c polish (the originally-planned scope, do this after Task 1 is verified working)

Per `PHASE_7A_COMPLETION_REPORT.md`'s and `PHASE_7B_COMPLETION_REPORT.md`'s
deferred-items lists, Phase 7c covers:

1. **Django-template staff views removal** (deferred from 7a) — now that
   7a built React/DRF replacements for `scraper_dashboard` and
   `health_monitor`, confirm the replacements are fully equivalent
   (compare feature-by-feature) and then remove the old
   `@staff_member_required` template views + their templates. Keep the
   removal as a separate, easily-revertible commit.
2. **TalentDiscovery `was_discoverable_at_creation`** (deferred from 7a)
   — add the model migration + consent-snapshot logic so a talent pool
   discovery record captures whether the candidate was discoverable AT
   THE TIME of discovery (protects against a later consent withdrawal
   retroactively making a past, legitimate discovery look like a
   violation).
3. **GDPR export/delete admin actions** (deferred from 7a, "dashboard
   counts only, not the full workflow") — build the actual DRF endpoint +
   confirmation flow + `ActivityLog` entry for BOTH a per-user data
   export (JSON dump: profile, CV, applications, interview data,
   conversation history) and a delete/anonymize action. The delete
   action must require a typed confirmation (e.g. admin re-enters the
   target user's email) before executing, given it's irreversible.
4. **Analytics polish** (deferred from 7b.3) — per-company AI cost
   breakdown (join through employer profiles, now that per-user
   breakdown works per the 7b.3 fix).
5. **Cmd+K quick-open for admin search** (deferred from 7b.4, explicitly
   called "nice-to-have") — only build this if Tasks 1-4 and the items
   below are done with time to spare; it's genuinely optional polish.
6. **Propose-confirm pattern for the Admin Copilot** (deferred from
   7b.1) — the copilot's 5 tools are currently all read-only, so this
   wasn't urgent, but if you add ANY new tool in this pass that changes
   state, it MUST use the propose→confirm→execute→audit pattern from the
   original Phase 7b prompt — do not add a destructive one-shot tool call
   even under time pressure.
7. **Final full-platform re-verification**: re-run
   `audit/prompts/LIVE_VERIFICATION_PROMPT.md`'s engine-by-engine live
   HTTP check one more time (all 11 engines), specifically re-testing
   Rashid AI (engine 8) now that Task 1's fix is in — this is the one
   engine that should change verdict from PARTIAL PASS to a real PASS or
   a clearly-stated remaining blocker (if AWS Bedrock model access is
   still the limiting factor even with the agent correctly wired, say so
   explicitly).

## Rules

- Local commits only, do not push — you push via Claude Code in Visual
  Studio yourself.
- Do not weaken `is_discoverable` consent enforcement anywhere.
- No payment/billing code.
- Real test coverage for every new/changed endpoint with side effects.
- Run full backend test suite + `npx tsc --noEmit` + `npx vite build
  --mode production` before considering Phase 7c complete.

## When done

Write `audit/PHASE_7C_COMPLETION_REPORT.md` covering Task 2's 7 items
(Task 1 gets its own report per above, since it's a critical fix, not
polish). At the very end, answer directly: **"Is Rashid AI now a real,
working tool-calling assistant end-to-end, or does a gap remain?"** — a
real yes/no-with-exceptions, not a hedge, matching the standard set by
every prior phase's final verdict.

## After Phase 7c

This closes the Admin Governance track (Phase 7 in full) and the
Rashid-agent-wiring gap. At that point the only remaining named,
deliberately-deferred work in this project is:
- **Phase 8 (Billing)** — `audit/prompts/PHASE_8_BILLING_PROMPT.md`,
  explicitly marked "do not run until you decide to monetize" — a
  business decision, not a technical readiness gap.
- **Human action items** repeated across every phase report and never
  yet confirmed done: AWS Bedrock model access request for
  `claude-sonnet-4-5-20250929-v1:0` in the target AWS account, AWS IAM
  permissions for Polly/Transcribe/S3 (voice interviews), a valid
  `JUDGE0_API_KEY`, AWS access key rotation (`AKIAYK...TGPY`), and
  provisioning real Redis + ClamAV in the production deployment target.
  None of these are code-fixable — they require the platform owner's
  direct action in AWS/third-party consoles.
- Whatever new gaps Phase 7c's own re-verification pass surfaces — read
  its final report before assuming the project is fully closed out.
