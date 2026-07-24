---
id: 2026-07-23T13-38-08Z-structured-outline-platform-lengths
date: "2026-07-23T13:38:08Z"
participants: [user, codex]
models: [gpt-5, deepseek-v4-flash]
tags:
  [
    backend,
    frontend,
    story-seed,
    structured-outline,
    novel,
    length-profile,
    browser,
  ]
related_paths:
  - ai-pic-backend/app/schemas/story_seed.py
  - ai-pic-backend/app/services/story/story_seed_service.py
  - ai-pic-backend/app/services/story/story_seed_structure_service.py
  - ai-pic-backend/app/services/story/story_novel_length_service.py
  - ai-pic-backend/app/services/story/story_novel_revision_service.py
  - ai-pic-frontend/src/components/features/stories/StoryStructuredOutlineEditor.tsx
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelLengthPanel.tsx
  - docs/design/story-novel-episode-script.md
  - docs/exec-plans/active/structured-outline-platform-lengths.md
summary: Deliver the StorySeed v2 outline and Revision-owned length implementation, with focused and partial real-UI evidence but no completed long-novel acceptance.
---

## User Prompt

Make the confirmed StorySeed chapter list the only source of novel chapter
structure. Move platform presets, custom character ranges, per-chapter
overrides, model selection, generation state, and approval evidence into each
Novel Revision. Generate sequentially from the frozen plan without a whole-book
target or application chapter cap.

## Goals

- Upgrade editable StorySeed drafts to a complete, confirmable
  `story_seed_v2.structured_outline`.
- Resolve every chapter's min/target/max range from a Revision-owned profile or
  override and derive whole-plan totals.
- Freeze outline, range, model, hashes, and plan version at dispatch while
  preserving legacy prose and Zhihu compatibility.
- Prove endpoint/service boundaries and real operator UI behavior without
  overstating incomplete model generation.

## Changes

- Added StorySeed v2 contracts, complete contiguous chapter validation,
  ending-direction coverage, explicit asynchronous structuring, and editable
  add/delete/reorder/split/merge UI.
- Revalidated both `StorySeedModel` values and endpoint
  `model_dump(by_alias=True)` dictionaries at the StorySeed service boundary.
- Made structuring use the Story's configured model or the stable
  `deepseek:<DEEPSEEK_DEFAULT_MODEL>` fallback.
- Added short/standard/long/custom Revision length profiles, per-chapter
  overrides, finite `min <= target <= max` validation, locally derived totals,
  and generation-plan v4 evidence.
- Added length-profile, StorySeed, Revision update/generation API contracts and
  operator controls for totals, locking, mismatch, body, extraction, and resume
  status.
- Preserved chapter-specific length gates, provider-aware output budgets,
  bounded repair, extraction-only resume, source/hash isolation, and legacy
  Zhihu behavior.

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
  — 39 passed. The StorySeed portion proves dictionary-boundary validation and
  configured/default planning-model resolution; the wider group proves the
  plan/body/resume invariants inherited by the structured plan.
- Chrome DevTools was attempted first but
  `http://127.0.0.1:9222/json/version` returned HTTP Not Found. Through the
  Chrome extension fallback, the real UI confirmed a 48-chapter StorySeed v2
  for Story `702dcae4a23c4533ae11f0d2e2a69eda` and created standard-serial
  Revision `53dee6c31d8d4f0eada05bb0e45eb0b3`.
- Task `#6513` records the initial structuring failure on an unavailable
  Volcengine model and `#6514` the successful DeepSeek structuring retry.
  Novel tasks `#6515`–`#6518` preserve Canon/plan failure and cancellation
  evidence; `#6519` remains in `planning/chapters` with 0/48 bodies.
- Persisted DeepSeek text invocations `#372`–`#384` are provider-attempt
  evidence only. They do not prove a completed profile-based novel, two
  isolated Revisions, or blocker-free approval.
- `python scripts/check_repo_docs.py` — passed.
- `python scripts/check_repo_contracts.py --mode diff <seven allowed
docs/ledger paths>` — exited successfully; the checker reported that no
  changed-file diff rules applied to this documentation-only slice.
- `git diff --check -- <seven allowed docs/ledger paths>` — passed.
- Backend quick/full, frontend lint/test, pre-commit, production image build,
  complete console/network capture, full real-model generation, and GPT-5.6
  review are not complete and are not claimed.

## Next Steps

- Complete current planning and generation without treating provider success as
  deterministic-plan success.
- Exercise at least one real chapter override and a second differently
  configured Revision, then prove plan, candidate, memory, and future-state
  isolation.
- Run all backend, frontend, repository, pre-commit, and production image gates.
- Complete browser console/network evidence and keep the Revision unapproved
  until every range, extraction, continuity, and approval requirement passes.

## Linked Commits

- This commit.
