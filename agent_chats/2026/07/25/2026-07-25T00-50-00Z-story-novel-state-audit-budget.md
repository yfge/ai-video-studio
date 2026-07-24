---
id: 2026-07-25-story-novel-state-audit-budget
date: 2026-07-25
participants:
  - user
  - codex
models:
  - gpt-5.6
tags:
  - story-novel
  - state-audit
  - output-budget
related_paths:
  - ai-pic-backend/app/services/story/story_novel_state_extraction.py
  - ai-pic-backend/tests/unit/test_story_novel_state_evidence_patch.py
summary: Raise long-form typed-state extraction to the supported 16000-token budget.
---

## User Prompt

Continue the real 48-chapter Canon-gated novel generation without the old 8192
output ceiling and preserve complete future-event auditing.

## Goals

- Prevent reasoning tokens from truncating the all-future-events audit.
- Keep the exact future catalog coverage and source-evidence gates unchanged.

## Changes

- Increased long-form typed-state extraction from 6000 to 16000 output tokens.
- Kept the evidence-only patch budget at 3000 because it returns only two small
  quote maps and never receives the future catalog.
- Added an explicit token-budget regression.

## Validation

- Formal Task 6624 invocation 1301 used DeepSeek V4 Pro with 17,314 prompt
  tokens, 17,280 cached tokens and 6,000 completion tokens; it ended with
  `finish_reason=length`.
- The bounded repair invocation 1302 used 18,309 prompt tokens, 17,280 cached
  tokens and 5,226 completion tokens, then failed the state gate. Chapter 1 and
  chapter 2 body hashes remained unchanged.
- `cd ai-pic-backend && pytest -q --no-cov
  tests/unit/test_story_novel_state_evidence_patch.py
  tests/unit/test_story_novel_state_extraction_repair.py` -> 5 passed.
- `cd ai-pic-backend && pytest -q --no-cov
  tests/unit/test_story_novel_*.py
  tests/unit/services/test_narrative_memory_*.py` -> 428 passed, 1 skipped.
- Exact `isort --check-only --profile=black` and `black --check` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ...` -> passed.
- `git diff --check` -> passed.
- `./docker/build_prod_images.sh` -> passed against this source tree; the image
  tag still reflected the pre-commit HEAD and is rebuilt after commit.

## Next Steps

- Rebuild the production images from the committed source.
- Restart the formal backend and worker.
- Resume the same Revision and require chapter 1 hash preservation.

## Linked Commits

- This commit.
