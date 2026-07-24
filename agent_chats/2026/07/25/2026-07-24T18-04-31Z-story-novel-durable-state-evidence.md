---
id: 2026-07-25-story-novel-durable-state-evidence
date: 2026-07-25
participants:
  - user
  - codex
models:
  - gpt-5.6
tags:
  - story-novel
  - source-evidence
  - typed-state
related_paths:
  - ai-pic-backend/app/services/story/story_novel_state_evidence_diagnostics.py
  - ai-pic-backend/app/services/story/story_novel_state_extraction.py
  - ai-pic-backend/app/services/story/story_novel_state_extraction_prompt.py
summary: Keep typed state durable and repair source evidence without weakening gates.
---

## User Prompt

Continue the formal 48-chapter novel run through the real API, MySQL and paid
models while preserving strict Canon, state, future and source-evidence gates.

## Goals

- Repair rewritten evidence prefixes only when the same actor is present in the
  same source sentence.
- Extract chapter-end durable state instead of temporary tool operations.
- Reject invalid `location`, `knowledge` and `possessions` fields at the typed
  extraction boundary before evidence-only repair can freeze them.

## Changes

- Added a unique exact-source candidate for a rewritten action lead only when
  the omitted actor token occurs exactly once earlier in the same sentence.
- Kept wrong-actor dialogue and action fragments fail-closed.
- Clarified that typed state represents durable chapter-end values, object
  locations follow their owner, and location never belongs in
  `state_transitions`.
- Added an early typed-delta contract issue so invalid state fields use the
  bounded full extraction repair instead of the quote-only patch.

## Validation

- Formal Task 6625 generated a new 4,019-character chapter 2 body.
- Invocation 1303: DeepSeek V4 Pro, 7,596 input, 7,552 cache, 4,877 output,
  `finish_reason=stop`, response hash `7ec0f1254b7b35ed...`.
- Invocation 1304 used the new 16,000-token state budget: 17,844 input, 7,487
  output, `finish_reason=stop`, response hash `49e86f10f8eb5de6...`.
- Invocation 1305 was the bounded 3,000-token evidence patch and ended `stop`;
  it still repeated a rewritten actor prefix, so the gate stopped before state
  application or Narrative Memory extraction.
- Offline read-only replay of invocation 1304 found the exact source candidate
  `从工装内袋里掏出自己的终端` at chapter offset 1858 and retained wrong-actor
  negative tests.
- Targeted evidence/state tests -> 14 passed.
- Full Story Novel and Narrative Memory unit scope -> 431 passed, 1 skipped.
- Exact `isort --check-only --profile=black` and `black --check` -> passed.
- `python scripts/check_repo_docs.py` and targeted repository contracts -> passed.
- `git diff --check` -> passed.
- `./docker/build_prod_images.sh` -> passed against the exact source tree; the
  images are rebuilt under the new commit hash after commit.

## Next Steps

- Complete format, repository-contract and production-image checks.
- Restart the formal backend and worker after a clean commit.
- Resume only Revision `1fe57d4e72dd45f19281c3c524c2fbce` and require
  chapter 1 and the saved chapter 2 body hashes to remain unchanged.

## Linked Commits

- This commit.
