# Continuation — Finish Phase 2, then run Phase 3

## Critical correction first

A prior run of this session built `EmployerTeamMember` (multi-seat
employer model + migration) for item 2.8 despite that item being
EXPLICITLY marked RESOLVED/SKIP in `audit/prompts/PHASE_2_PROMPT.md`. This
has already been reverted by the human (model/migration deleted, verified
zero other code referenced it). **Do NOT rebuild `EmployerTeamMember` or
any hiring-team/multi-seat model.** Items 2.8 and 2.22 are both
permanently SKIP for this pass — do not revisit them.

## Remaining Phase 2 work

Read `audit/prompts/PHASE_2_PROMPT.md` again for full context. Every item
except 2.8 and 2.22 (both explicitly skipped) should now be done — verify
by reading `git log --oneline` since commit `3a92ce0`, and re-check each
item 2.1-2.22 (except 2.8/2.22) against current code. Item **2.17** is the
one confirmed still open: decide the fate of `apps/config/ai_config.py` (or
find its actual current path — it may have moved) — a fully dead, unwired
cost-optimization module. Check if anything imports/calls it
(`grep -rn` for its key functions/classes across `backend/apps/`). If truly
zero callers: either wire it into the consolidated model router
(from Phase 1's `MODEL_ALIASES` work) as a real cost-optimization path, OR
delete it if the added complexity isn't worth it — pick delete unless you
find a clear, low-risk wiring point, and say which you chose and why in the
completion report.

Also double check 2.1, 2.9, 2.3, 2.12 (there were some very early partial
fixes from an interrupted prior run before this session properly started —
verify they are fully correct now, not just partially patched).

When Phase 2 is fully done, write/update
`audit/PHASE_2_COMPLETION_REPORT.md` per the format specified at the
bottom of `audit/prompts/PHASE_2_PROMPT.md` — cover all 22 items
including explicitly noting 2.8 and 2.22 as "SKIPPED per resolved decision,
do not build."

## Then: run Phase 3

Read `audit/prompts/PHASE_3_PROMPT.md` in full and execute all 11 items
(3.1-3.11) exactly as scoped there. Write
`audit/PHASE_3_COMPLETION_REPORT.md` when done.

## Then: final consolidated status

Read all 4 completion reports (`audit/PHASE_0_COMPLETION_REPORT.md`
through `PHASE_3_COMPLETION_REPORT.md`) and write
`audit/ALL_PHASES_FINAL_STATUS.md` — a short final-delta summary (not a
restatement): what's now fixed platform-wide across all 4 phases, what
remains a human action item (should be exactly 3: AWS Polly/Transcribe
perms, JUDGE0_API_KEY, AWS key rotation confirmation), and any NEW issue
discovered during implementation that wasn't in the original 10 domain
audits or MASTER_IMPLEMENTATION_PLAN.md.

## Rules (same as before)

- Local git commits only, do NOT push.
- Never read/print/commit `backend/.env`.
- Run tests after each fix where tests exist.
- Commit logically-grouped changes separately with clear messages.
