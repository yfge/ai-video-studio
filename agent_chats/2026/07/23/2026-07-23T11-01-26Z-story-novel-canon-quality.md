---
id: 2026-07-23T11-01-26Z-story-novel-canon-quality
date: "2026-07-23T11:01:26Z"
participants: [user, codex]
models: [gpt-5, deepseek-v4-flash]
tags: [backend, frontend, story, novel, canon, continuity, browser, real-model]
related_paths:
  - ai-pic-backend/app/services/story/story_novel_canon_service.py
  - ai-pic-backend/app/services/story/story_novel_milestone_state.py
  - ai-pic-backend/app/services/story/story_novel_plan_checkpoint.py
  - ai-pic-backend/app/services/story/story_novel_state_validator.py
  - ai-pic-backend/app/services/story/story_novel_task_processor.py
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelCanonPanel.tsx
  - docs/design/story-novel-episode-script.md
  - docs/design/narrative-memory-and-dramatic-state.md
  - docs/exec-plans/active/canon-gated-longform-quality-loop.md
summary: Add fail-closed Canon and typed state gates, then record partial real UI and model-planning evidence without claiming full-novel acceptance.
---

## User Prompt

Implement the Canon-gated long-form quality plan: compile a unique Canon before
planning prose, validate state changes extracted from each actual chapter,
allow human-confirmed Canon repair plus earliest-safe resume, add deterministic
continuity/approval gates and editorial scores, and prove the result with a new
48-chapter real-model novel and GPT-5.6 review.

## Goals

- Preserve the existing 3000–5000 non-whitespace-character sequential
  generation, checkpoint/resume, and revision-local Narrative Memory behavior.
- Add fail-closed Canon and chapter contracts without a new database,
  vector store, or dependency.
- Prevent an invalid chapter from changing current state or contaminating
  later prompts, facts, memories, or Story Canon.
- Let operators review and explicitly save Canon repairs, then regenerate from
  the earliest affected chapter.
- Separate deterministic approval gates from model editorial judgment.
- Keep legacy Zhihu and old generation-plan revisions compatible, and never
  restore a fixed 8192-token long-form output ceiling.

## Changes

- Added typed Canon, chapter-contract, and state-delta schemas plus focused
  Canon validation/hash/diff, hard-context, actual-body state extraction,
  state validation/application, chapter gate, and v2 checkpoint services.
- Added strict Canon `gate_version=1` and entity-backed milestone typed outcomes.
  Future outcomes are rejected at chapter-zero Canon validation, deterministic
  whole-plan replay, and actual-body state validation. Knowledge changes use
  source-event-backed `knowledge_grants`, never ordinary state transitions.
- Closed future-outline leakage: prose chapter N now receives only its current
  frozen structured-outline contract, while an independent audit-only state
  extractor can classify premature future events without exposing later
  contracts to the prose or repair calls.
- Made planning checkpoint reuse fail closed: failed/old-gate/invalid/hash-stale
  Canon is recompiled; only a hash-valid gated Canon may be reused for
  chapter-contract repair, while a failed chapter plan is never reused.
- Split planning into Canon and chapter-contract phases with one repair each;
  long-form planning and global review can pass a 16000-token output budget.
- Upgraded new-revision evidence to `story_novel_generation_plan.v2`,
  `story_novel_continuity.v3`, and
  `story_novel_continuity_review.v3`.
- Added deterministic quality metrics, complete state-hash-chain validation,
  repair groups, independent editorial scores, and stricter approval
  requirements.
- Added optimistic Canon PATCH, earliest affected chapter invalidation, and
  explicit resume semantics; local Canon saving does not call a model.
- Added Canon editing, quality overview, state-validation progress, gate
  failure, stale-range resume, endpoint/types, and focused frontend coverage.
- Revalidated endpoint-dumped StorySeed dictionaries at the service boundary
  and made StorySeed structuring use the Story model or the stable
  `deepseek:<DEEPSEEK_DEFAULT_MODEL>` fallback.
- Updated both narrative design sources, `tasks.md`, `docs/README.md`, and the
  active execution plan while preserving the separate structured-outline and
  platform-length work.

## Validation

- Latest focused backend command:
  `pytest
tests/unit/test_story_novel_canon_state.py
tests/unit/test_story_novel_planning_contract.py
tests/unit/test_story_novel_future_outline_isolation.py
tests/unit/test_story_novel_chapter_state_gate.py
tests/unit/test_story_novel_state_chain.py
tests/unit/test_story_novel_longform_recovery.py
tests/unit/test_story_novel_chapter_contract.py
tests/unit/test_story_seed_structure_model.py
tests/unit/services/test_story_seed_invalidation.py -q -o addopts=''`
  — 39 passed. This covers milestone outcomes, chapter-zero/plan/body gates,
  future-information isolation, planning checkpoint reuse, extraction resume,
  StorySeed dictionary validation, and planning-model selection.
- Chrome DevTools was attempted first but
  `http://127.0.0.1:9222/json/version` returned HTTP Not Found. The Chrome
  extension fallback exercised the real UI at
  `http://localhost:8089/stories/702dcae4a23c4533ae11f0d2e2a69eda`:
  the 48-chapter StorySeed v2 was confirmed, standard-serial Revision
  `53dee6c31d8d4f0eada05bb0e45eb0b3` was created, and generation tasks were
  started. This is fallback UI evidence, not Chrome DevTools verification.
- Real task evidence is deliberately recorded as partial:
  `#6513` structuring failed on an unavailable Volcengine model; `#6514`
  structuring completed; `#6515` and `#6517` failed Canon validation; `#6516`
  was cancelled after Canon while planning chapters; `#6518` failed chapter
  planning; and `#6519` remains processing in `planning/chapters`. The Revision
  still has 0/48 generated bodies.
- Persisted text invocations `#372`–`#384` use DeepSeek V4 Flash and succeeded
  at the provider layer. Several recorded output-token counts exceed 8192,
  proving those requests were not clipped by the former fixed ceiling, but the
  downstream deterministic task failures remain authoritative.
- `python scripts/check_repo_docs.py` — passed.
- `python scripts/check_repo_contracts.py --mode diff <seven allowed
docs/ledger paths>` — exited successfully; the checker reported that no
  changed-file diff rules applied to this documentation-only slice.
- `git diff --check -- <seven allowed docs/ledger paths>` — passed.
- Backend quick/full, frontend lint/test, pre-commit, production image build,
  the remaining browser repair/resume/approval path, completed real-model
  generation, and GPT-5.6 review have not completed and are not claimed.

## Next Steps

- Observe task `#6519` without treating provider success as planning success;
  if it fails, retain Canon/plan error evidence and resume only through the
  validated checkpoint rules.
- Complete focused API/approval/invalidation/frontend coverage and all
  repository gates required by `AGENTS.md`.
- Continue the Chrome extension fallback path through chapter gate failure,
  Canon repair, earliest-range resume, continuity review, and approval while
  preserving console/network evidence.
- Generate 48/48 bodies, prove one real resume, run GPT-5.6 eight-batch plus
  global review, and keep the Revision unapproved unless every deterministic
  and editorial threshold passes.
- Update this record's Validation and move the active exec plan only after
  durable evidence exists.

## Linked Commits

- This commit.
