---
id: 2026-07-25-story-novel-evidence-repair-candidate
date: 2026-07-25
participants:
  - user
  - codex
models:
  - gpt-5.6
tags:
  - story-novel
  - evidence
  - longform
related_paths:
  - ai-pic-backend/app/services/story/story_novel_state_evidence_diagnostics.py
  - ai-pic-backend/tests/unit/test_story_novel_state_evidence_diagnostics.py
  - ai-pic-backend/tests/unit/test_story_novel_state_evidence_patch.py
summary: Provide an exact current-chapter quote candidate when evidence rewrites one safe leading character.
---

## User Prompt

Continue the real 48-chapter Canon-gated novel generation and quality acceptance.

## Goals

- Recover chapter 2 from an evidence-only checkpoint without rewriting its body.
- Keep source-evidence validation fail-closed.
- Avoid another blind prose regeneration or manual database edit.

## Changes

- Added a diagnostic-only fallback for a unique source-backed suffix when the
  model rewrites one safe leading pronoun or disposal marker.
- Dialogue attribution and named actors are not rewritten.
- Added diagnostics and end-to-end evidence-only repair regressions.

## Validation

- `pytest --collect-only -q tests/unit/test_story_novel_state_evidence_diagnostics.py tests/unit/test_story_novel_state_evidence_patch.py --no-cov`
  -> 9 tests collected.
- `pytest -q --no-cov tests/unit/test_story_novel_state_evidence_diagnostics.py tests/unit/test_story_novel_state_evidence_patch.py`
  -> 9 passed.
- `pytest -q --no-cov tests/unit/test_story_novel_*.py tests/unit/services/test_narrative_memory_*.py`
  -> 427 passed, 1 skipped.
- Exact `isort --profile=black --check-only` and `black --check` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed paths>` -> passed.
- `git diff --check` -> passed.
- `./docker/build_prod_images.sh` -> backend and frontend multi-platform builds
  completed successfully.
- Real MySQL read-only reproduction: chapter 2 remains a 3386-character
  `state_pending` checkpoint with body hash
  `068b9bef0d7452afa2fc3e341656faf7c504675951cd0ce757a0d66113675eb2`.
  The failed quote contained `他从工具包里掏出六根钛合金标尺`; the source
  contains the unique exact suffix `从工具包里掏出六根钛合金标尺`.

## Next Steps

- Restart the mounted backend and worker after the clean commit.
- Resume the current Revision through the formal API and verify chapter 2 body
  hash remains unchanged.

## Linked Commits

- This commit.
