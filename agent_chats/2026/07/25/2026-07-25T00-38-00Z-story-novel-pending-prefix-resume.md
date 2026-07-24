---
id: 2026-07-25-story-novel-pending-prefix-resume
date: 2026-07-25
participants:
  - user
  - codex
models:
  - gpt-5.6
tags:
  - story-novel
  - resume
  - checkpoint
related_paths:
  - ai-pic-backend/app/services/story/story_novel_chapter_checkpoint.py
  - ai-pic-backend/tests/unit/test_story_novel_state_pending_drift.py
summary: Preserve a later state-pending recovery while replaying ready prefix chapters.
---

## User Prompt

Continue the formal 48-chapter generation and prove Resume does not rewrite
completed chapter bodies or hashes.

## Goals

- Allow extraction-only recovery at chapter 2 after replaying ready chapter 1.
- Keep all body, source, context, Canon, and state hash checks fail-closed.

## Changes

- `finalize_state` now keeps the revision-wide state status failed while
  `recovery_from_position` points to a later chapter.
- The recovery marker is still removed only when that exact chapter is
  successfully finalized.
- Added a regression for a ready prefix before a later pending checkpoint.

## Validation

- `pytest --collect-only -q --no-cov tests/unit/test_story_novel_state_pending_drift.py tests/unit/test_story_novel_state_pending_resume.py`
  -> 5 tests collected.
- `pytest -q --no-cov tests/unit/test_story_novel_state_pending_drift.py tests/unit/test_story_novel_state_pending_resume.py`
  -> 5 passed.
- `pytest -q --no-cov tests/unit/test_story_novel_*.py tests/unit/services/test_narrative_memory_*.py`
  -> 428 passed, 1 skipped.
- Exact `isort --profile=black --check-only` and `black --check` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed paths>` -> passed.
- `git diff --check` -> passed.
- `./docker/build_prod_images.sh` -> backend and frontend multi-platform builds
  completed successfully.
- Formal API Task 6623 reproduced the defect without a provider call: it
  failed before chapter 2 with `待恢复状态与当前计划不一致`; chapter 1 and 2
  hashes remained unchanged.

## Next Steps

- Restart the formal backend and worker after a clean commit.
- Resume Revision `1fe57d4e72dd45f19281c3c524c2fbce` once and verify chapter
  2 performs state extraction without changing its body hash.

## Linked Commits

- This commit.
