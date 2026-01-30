---
id: 2026-01-28T09-35-39Z-backend-structured-output-repair-utils
date: 2026-01-28T09:35:39Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, ai, validation]
related_paths:
  - ai-pic-backend/app/services/ai/structured_output.py
  - ai-pic-backend/tests/unit/services/ai/test_structured_output.py
summary: "Introduced a shared structured-output parse/validate/repair helper for AI JSON outputs with unit tests."
---

## User Prompt

Follow `tasks.md` to improve story/episode generation quality with strict validation + repair, context management, and readiness checks.

## Goals

- Create a reusable, tested helper for strict JSON extraction + Pydantic validation.
- Provide a generic repair loop that can be reused by story outline and episode plan generation.

## Changes

- Added `ai-pic-backend/app/services/ai/structured_output.py`:
  - `validate_payload()` for JSON extraction + optional normalization + Pydantic validation.
  - `generate_with_repair()` for AI manager calls with up to N repair attempts and structured attempt metadata.
- Added unit tests in `ai-pic-backend/tests/unit/services/ai/test_structured_output.py`.

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/ai/test_structured_output.py -q`
- `./docker/build_prod_images.sh`

## Next Steps

- Integrate this helper into story outline + episode plan generation so invalid outputs are repaired (or rejected) before persistence.

## Linked Commits

- (this commit)
