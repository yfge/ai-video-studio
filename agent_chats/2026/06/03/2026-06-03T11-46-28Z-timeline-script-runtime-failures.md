---
id: 2026-06-03T11-46-28Z-timeline-script-runtime-failures
date: "2026-06-03T11:46:28Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, timeline-pipeline, script-generation, celery]
related_paths:
  - ai-pic-backend/app/services/audio/dialogue_processing/scene_extractors.py
  - ai-pic-backend/app/services/script_quality_gate.py
  - ai-pic-backend/app/services/script_quality_gate_auto_characters.py
  - ai-pic-backend/app/services/script_quality_gate_repair_guard.py
  - ai-pic-backend/tests/unit/services/audio/test_scene_extractors_legacy_columns.py
  - ai-pic-backend/tests/unit/services/test_script_quality_gate_runtime_failures.py
summary: "Fix timeline scene audio extraction and script gate handling for runtime failures"
---

## User Prompt

一键时间轴流水线 - 程序员之我家掉下来个？林妹妹？七仙女？不！是个锅盖～～～～ / 第1集 从天而降的锅盖
失败
进度：missing_scene_dialogue_audio: 1, 2, 3

Timeline pipeline for script 128

生成剧本 - 剧集155
失败
进度：script speakers must be registered story or episode characters; script lint must pass

## Goals

- Diagnose the `missing_scene_dialogue_audio: 1, 2, 3` timeline pipeline failure for script 128.
- Diagnose the episode 155 script generation quality gate failure.
- Make the narrow backend fixes needed for these runtime failure modes.
- Restart the Celery worker after the fix so async tasks load the updated code.

## Changes

- Updated scene dialogue/stage extraction to read `Script.dialogues` and `Script.stage_directions` JSON columns when `Script.content` is legacy rendered text.
- Added a script quality gate step that auto-creates real Episode temporary characters for unknown speakers that can be extracted from script dialogues, then re-runs the gate.
- Kept the auto-create path heuristic-only by passing `ai_service=None`, avoiding an extra model call and old/new AI manager interface mismatch.
- Added a repair structure guard so AI repair output that drops scenes, dialogues, stage directions, or collapses substantial content is rejected instead of replacing a better script candidate.
- Added focused regression tests for legacy script column extraction, temporary speaker registration, and repair structure loss.
- Restarted `ai-video-celery-worker`; container status after restart was `Up 10 seconds`.

## Validation

1. Runtime evidence:

- `docker exec -i ai-video-backend python - ...` for script 128 showed `content` type `str`, `12` dialogues, `3` stage directions.
- The same check showed scene extraction counts: scene 1 `2` dialogues / `1` stage direction, scene 2 `4` / `1`, scene 3 `6` / `1`.

2. Targeted backend tests:

- `cd ai-pic-backend && pytest tests/unit/services/audio/test_dialogue_processor.py tests/unit/services/audio/test_scene_extractors_legacy_columns.py tests/unit/services/test_narrative_quality_gate.py tests/unit/services/test_script_quality_gate_runtime_failures.py -q` -> pass, `55 passed`.
- `cd ai-pic-backend && pytest tests/unit/services/audio/test_scene_extractors_legacy_columns.py tests/unit/services/test_script_quality_gate_runtime_failures.py tests/unit/services/test_narrative_quality_gate.py -q` -> pass, `11 passed`.

3. Repository checks:

- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff ...` for the changed runtime-failure files -> pass.

4. Blocked broader backend quick check:

- `cd ai-pic-backend && python run_tests.py quick` did not reach tests. It failed during dependency installation because Python 3.13 dependency resolution conflicts with repo pins: `langchain-core==0.2.43` requires `pydantic>=2.7.4` while the repo pins `pydantic==2.5.0`.

5. Pre-commit:

- `pre-commit run --files ...` passed merge/whitespace/ruff/docs/contracts/ledger checks and reformatted three staged files.
- The same pre-commit run failed at its full backend pytest hook with 3 failures outside this fix's targeted surface: two `tests/unit/services/video/test_video_task_dispatcher.py` failures in the dirty, unrelated video worktree changes, and `tests/scripts/test_script_dialogue_fallback.py::test_generate_script_dialogue_fallback` due live text-provider quality-gate calls failing (`deepseek` 402, Google/Volcengine 404, Minimax auth).
- After formatting, the targeted pytest and diff contracts listed above were rerun and passed.

## Next Steps

- Re-run the failed UI tasks after the worker restart. The previous failed task rows remain historical failures.
- The unrelated provider/video worktree changes were left untouched and should be committed separately if still intended.

## Linked Commits

- Not committed yet.
