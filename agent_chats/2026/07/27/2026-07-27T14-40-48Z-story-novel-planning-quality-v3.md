## User Prompt

Implement the chapter-planning long-form novel quality pipeline v3: explicit
StorySeed chapter count and planning model, a frozen planning/prose/audit model
policy, Event/Memory input only for chapter planning, block prose generation,
proof-only audit, deterministic state and Narrative materialization, bounded
local repair, evidence-only recovery, v3 approval/downstream gates, and a real
48-chapter paid acceptance with cancel/Resume and GPT-5.6 review.

## Goals

- Prevent future-outline, raw Narrative Memory, and audit/state instructions
  from leaking into prose generation.
- Make each chapter's brief, prose blocks, sentence proofs, expected state
  delta, candidates, invocation evidence, and hash chain durable and replayable.
- Preserve legacy v2 reading/resume while making production adaptation depend
  on an approved canonical v3 Revision.
- Prove the complete chain with repository validation and a new real API/MySQL
  48-chapter run before approval.

## Changes

- Added `story_novel_generation_plan.v3`, `story_novel_continuity.v4`, frozen
  three-stage model policy, chapter brief/block contracts, future guard index,
  sentence span/proof audit, server-owned expected delta, and deterministic
  Event/Memory materialization.
- Added atomic prose checkpointing, bounded local block repair, evidence-only
  and candidate-only Resume, exact invocation-response binding, tamper-resistant
  approval checks, and canonical-v3 downstream enforcement.
- Added a server-owned global plan state compiler, persistent/scene Canon
  location hierarchy, full structural diagnostics, targeted plan patches,
  complexity-adaptive batches, and missing/unsupported semantic effect audit.
- Added deterministic Event/Memory planning relevance, partial-block recovery
  for truncated prose, and product-level invocation rejection metadata while
  preserving transport success.
- Added frontend planning/prose/audit model selectors and v3 chapter-stage,
  call, token, latency, and failed-block status.
- Hardened the plan semantic-audit adapter after a real DeepSeek response used
  the exact event skeleton as a top-level array: that equivalent shape is now
  normalized before the unchanged event-order, ID, typed-effect, and Canon
  validation, while the prompt explicitly requires a top-level `events` object.
- Stabilized `future_guard_index` across MySQL JSON key ordering and runtime
  chapter mirrors by hashing only the frozen chapter contract in canonical key
  order. Legacy indexes may differ only in derived match terms; their index,
  claim fingerprints, protected conclusions, dates, entities, positions, and
  milestone bindings remain strictly verified.
- Updated both design sources, the docs index, task board, and the dedicated v3
  execution plan.

## Validation

- Focused hardening tests: `34 passed`.
- Story Novel unit suite before the final one-test compatibility correction:
  `487 passed, 1 skipped, 1 failed`; the remaining assertion is fixed and its
  exact regression now passes. A full rerun is pending.
- Backend quick-equivalent with external tests disabled: `3227 passed, 80
skipped, 20 deselected`; `run_tests.py quick` itself cannot start in this
  worktree because it requires a local `.venv` directory.
- Backend full suite with external tests disabled: `3230 passed, 97 skipped`.
- Frontend v3 focused suite: `6 passed`; lint: `0 errors, 3 existing warnings`;
  webpack production build passed.
- Frontend full suite: `482 passed, 10 failed`; failures are in existing
  Production Canvas ChatBar/Persistence/Planner fixtures and do not touch the
  Story Novel files. They remain a repository baseline issue, not a v3 pass.
- Repository docs, changed-path contracts, isort, black, and whitespace diff
  checks passed at the implementation checkpoint.
- Post-fix targeted semantic-audit suite: `19 passed`; post-fix complete Story
  Novel suite: `544 passed, 1 skipped`; black, isort, diff contracts, and file
  limits passed (`story_novel_plan_semantic_audit.py` is 250 lines).
- Real UI/API/MySQL task `6682` failed closed with zero chapters because
  invocation `1542` returned a valid top-level event array; the adapter fix was
  derived from that persisted provider response rather than a mock.
- Real Resume task `6683` completed the 48-chapter plan and generated a
  2,211-character chapter-one body (`body_hash=86dcd7fa...`) before GPT-5.6
  audit invocation `1560` failed with OpenAI `429 insufficient_quota`. The
  chapter remains `review_required` at audit stage; no state or Narrative
  candidate was promoted.
- A first Resume attempt (`6684`) exposed future-index drift before any provider
  call. The live persisted plan now passes `valid_v3_plan_fields` and
  `reusable_generation_plan`; focused tests passed `9/9`, and the full Story
  Novel suite passed `546` with `1 skipped`.
- A second formal UI Resume (`6685`) reused chapter one's exact body hash and
  reached GPT audit invocation `1561`; OpenAI again returned `429
insufficient_quota`. No prose call, state application, or Narrative
  promotion occurred, and no target task/invocation remains active.

## Next Steps

- Run all-file pre-commit and production image build; preserve exact unrelated
  baseline failures rather than folding Production Canvas fixes into this slice.
- Restore quota for the configured `openai:gpt-5.6-sol` provider, then use the
  official Resume endpoint to complete the existing audit-stage checkpoint and
  continue the public API/MySQL 48-chapter run. Do not regenerate chapter one.
- After at least two ready chapters, complete the official cancel/Resume hash
  proof before continuing to 48/48.
- Run eight GPT-5.6 six-chapter reviews plus one global synthesis, then approve
  and promote only if every deterministic and editorial gate passes.
- Populate the run artifact manifest and replace pending validation statements
  with current task, invocation, hash, browser, database, and review evidence.

## Linked Commits

- Pending exact-scope commits after real acceptance evidence is complete.
