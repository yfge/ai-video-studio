---
id: 2026-06-03T11-09-01Z-script-estimated-duration-normalization
date: "2026-06-03T11:09:01Z"
participants: [user, codex]
models: [gpt-5-codex]
tags: [backend, script-generation, quality-gate]
related_paths:
  - ai-pic-backend/app/services/script/content_normalization.py
  - ai-pic-backend/app/services/script/beat_contract_generation.py
  - ai-pic-backend/app/services/ai/scripts_ai_manager.py
  - ai-pic-backend/tests/unit/services/script/test_beat_contract_normalizer.py
  - ai-pic-backend/tests/unit/services/ai/test_scripts_ai_manager_failures.py
summary: Normalize numeric script duration metadata and preserve explicit provider failures.
---

## User Prompt

User reported failed async script-generation tasks from the Tasks UI:

- `Script for episode 87`, failed with progress `script schema invalid`, created 2026-06-03 10:54:58.
- `Script for episode 153`, failed with progress `AI剧本生成失败`, created 2026-06-03 10:53:53.

## Goals

- Identify the concrete failure evidence in the local task records.
- Fix the deterministic schema failure for episode 87.
- Improve the episode 153 failure path so explicit provider/model beat-contract failures are not collapsed into only `AI剧本生成失败`.
- Keep the change narrow and validated.

## Changes

- Queried local MySQL task records and found task `5996` for episode `87` failed because `metadata.estimated_duration` was integer `60`, while `ScriptModel.metadata.estimated_duration` expects a string.
- Added script content normalization that coerces non-string `metadata.estimated_duration` values to strings before quality-gate schema validation.
- Added unit coverage proving numeric `estimated_duration` normalizes to a `ScriptModel`-valid payload.
- Found task `5995` for episode `153` only persisted the generic `AI剧本生成失败`; the provider/beat-contract detail had already been lost.
- Made `BeatContractGenerationError` include provider error detail in its string form.
- Changed `ScriptManagerMixin._call_ai_manager_script()` to re-raise beat-contract generation errors when a provider or model was explicitly requested, preserving mock fallback behavior for non-explicit generation.
- Added focused unit coverage for explicit provider failure propagation.

## Validation

- DB inspection:
  - `task 5996`: `quality_gate.blocking_issues[0].details.error` was `metadata.estimated_duration` integer `60` failing string validation.
  - `task 5995`: `parameters.agent_run.error.message` was only `AI剧本生成失败`; no deeper provider detail remained in DB.
- Red tests:
  - `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_normalizer.py::test_content_normalization_coerces_numeric_estimated_duration_metadata -q` -> failed before implementation with `assert 60 == "60"`.
  - `cd ai-pic-backend && pytest tests/unit/services/ai/test_scripts_ai_manager.py::test_call_ai_manager_script_preserves_explicit_provider_failure -q` -> failed before implementation because `BeatContractGenerationError` was not raised.
- Green tests:
  - `cd ai-pic-backend && pytest tests/unit/services/ai/test_scripts_ai_manager_failures.py tests/unit/services/script/test_beat_contract_normalizer.py -q` -> passed, `7 passed`.
  - `cd ai-pic-backend && pytest tests/unit/services/ai/test_scripts_generation_mixin.py -q` -> passed, `2 passed`.
- Repository checks:
  - `python scripts/check_repo_docs.py` -> `[check_repo_docs] ok`.
  - `python scripts/check_repo_contracts.py --mode diff ...` is pending current-turn rerun before commit.
- E2E/browser:
  - Not run. Docker backend, celery worker, and nginx are running, but a true browser retry of the fixed script-generation path would require restarting the worker to pick up local code and would trigger external provider generation. This was intentionally not done in this narrow backend fix.

## Next Steps

- Restart the backend/celery containers before retrying episode `87` or `153` through the UI so the worker loads the patched code.
- Retry episode `153` with the same explicit model if provider behavior still needs investigation; the next failure should preserve the beat-contract/provider error instead of only `AI剧本生成失败`.

## Linked Commits

- Pending.
