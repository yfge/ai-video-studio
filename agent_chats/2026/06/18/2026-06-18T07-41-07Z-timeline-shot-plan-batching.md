---
id: 2026-06-18T07-41-07Z-timeline-shot-plan-batching
date: "2026-06-18T07:41:07Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - timeline
  - backend
  - shot-plan
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py
  - ai-pic-backend/app/services/ai/structured_output.py
  - ai-pic-backend/app/services/task_agent_run/builders_script_ops.py
  - ai-pic-backend/app/services/task_agent_run/persistence.py
  - ai-pic-backend/app/services/timeline_shot_plan_batching.py
  - ai-pic-backend/app/services/timeline_shot_plan_payloads.py
  - ai-pic-backend/app/services/timeline_shot_plan_service.py
  - ai-pic-backend/tests/integration/test_timeline_pipeline_errors.py
  - ai-pic-backend/tests/test_timeline_shot_plan_api.py
  - ai-pic-backend/tests/timeline_shot_plan_batch_helpers.py
  - ai-pic-backend/tests/timeline_shot_plan_test_helpers.py
summary: Batch Timeline shot-plan generation and persist sanitized failure diagnostics for large timelines.
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN: Fix Timeline Shot Plan JSON Truncation for task #6065. Do not automatically rerun task #6065, do not call live DeepSeek, and do not write a new Timeline version during validation.

## Goals

- Replace one large Timeline shot-plan request with batched generation for large video timelines.
- Keep each batch bounded with per-batch prompts, max token caps, and structured repair.
- Preserve full-plan validation before writing Timeline refs.
- Persist concise operator-facing failures plus structured non-raw diagnostics for task and agent-run analysis.
- Leave unrelated frontend dirty work and live recovery untouched.

## Changes

- Batched Timeline shot-plan generation into original-order groups of 8 video clips, with dialogue/subtitle context filtered to the batch.
- Added per-batch structured output repair with `max_repairs=2` and max tokens capped at `max(4000, min(12000, batch_clip_count * 1200))`.
- Merged validated batch plans, then retained existing full-plan clip, duration, and dialogue validation before Timeline update.
- Added JSON-safe Pydantic validation errors for structured-output repair prompts.
- Persisted sanitized pipeline error details into task parameters and `agent_run.error`, including batch index, clip ids, provider/model, usage, finish reason, token cap, and repair attempts.
- Added backend tests for 52-clip batching, batch repair success, and persisted pipeline failure diagnostics.

## Validation

- `cd ai-pic-backend && pytest tests/test_timeline_shot_plan_api.py::test_timeline_shot_plan_api_batches_large_timeline_without_truncation tests/test_timeline_shot_plan_api.py::test_timeline_shot_plan_api_repairs_invalid_batch_json -q` -> pass, 2 tests.
- `cd ai-pic-backend && pytest tests/integration/test_timeline_pipeline_errors.py::test_process_timeline_pipeline_persists_http_exception_detail -q` -> pass, 1 test.
- `cd ai-pic-backend && pytest tests/test_timeline_shot_plan_api.py::test_timeline_shot_plan_api_rejects_invalid_plan_without_updating tests/test_timeline_shot_plan_prompt_layers.py::test_timeline_shot_plan_api_rejects_motion_timeline_outside_clip_duration -q` -> pass, 2 tests.
- `cd ai-pic-backend && pytest tests/test_timeline_shot_plan_api.py tests/test_timeline_shot_plan_prompt_layers.py tests/integration/test_timeline_pipeline_import_api.py tests/integration/test_timeline_pipeline_errors.py -v` -> pass, 9 tests.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py ai-pic-backend/app/services/ai/structured_output.py ai-pic-backend/app/services/task_agent_run/builders_script_ops.py ai-pic-backend/app/services/task_agent_run/persistence.py ai-pic-backend/app/services/timeline_shot_plan_batching.py ai-pic-backend/app/services/timeline_shot_plan_payloads.py ai-pic-backend/app/services/timeline_shot_plan_service.py ai-pic-backend/tests/integration/test_timeline_pipeline_errors.py ai-pic-backend/tests/test_timeline_shot_plan_api.py ai-pic-backend/tests/timeline_shot_plan_batch_helpers.py ai-pic-backend/tests/timeline_shot_plan_test_helpers.py agent_chats/2026/06/18/2026-06-18T07-41-07Z-timeline-shot-plan-batching.md` -> pass.
- `git diff --check -- <tracked touched backend files>` -> pass.
- `git diff --check --no-index -- /dev/null <new backend helper or ledger file>` -> no whitespace error output for each new file; exit code 1 is expected for a new file diff.
- Commit-time recheck before split commit:
  - `python scripts/check_repo_docs.py` -> pass.
  - `python scripts/check_repo_contracts.py --mode diff <backend/frontend/ledger changed paths>` -> pass.
  - `git diff --check` -> pass.
  - `cd ai-pic-backend && pytest tests/test_timeline_shot_plan_api.py::test_timeline_shot_plan_api_batches_large_timeline_without_truncation tests/test_timeline_shot_plan_api.py::test_timeline_shot_plan_api_repairs_invalid_batch_json tests/integration/test_timeline_pipeline_errors.py::test_process_timeline_pipeline_persists_http_exception_detail -q` -> pass, 3 tests.
  - `pre-commit run --all-files` -> failed on existing all-repo issues (`ruff` historical files and pytest collection error in `tests/unit/services/ai/test_scripts_ai_manager.py`); unrelated EOF hook edits were restored before staging.
  - `./docker/build_prod_images.sh` -> pass; pushed backend and frontend production images with tag `068996e3`.
- Live provider/DB recovery: intentionally not run per user instruction; task #6065 was not retried.

## Next Steps

- None planned unless explicit recovery is requested for task #6065.

## Linked Commits

- This commit.
