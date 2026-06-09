---
id: "2026-06-09T12-15-58Z-dialogue-repair"
date: "2026-06-09T12:15:58Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - ai-video-studio
  - backend
  - dialogue
  - storyboard
  - timeline
summary: Repair fallback narration dialogue extraction and script 142 storyboard timeline data.
related_paths:
  - ai-pic-backend/app/services/script_dialogue_extraction.py
  - ai-pic-backend/app/services/script_missing_parts.py
  - ai-pic-backend/app/services/script_quality_gate.py
  - ai-pic-backend/app/services/audio/dialogue_processing/prose_dialogue_splitter.py
  - artifacts/runs/dialogue-repair-20260609-121418/
---

## User Prompt

`http://localhost:8089/episodes/340cacb9ed854bb18d50f2c69547bf03/workspace?tab=storyboard&scriptId=142 生成的对白还是有问题！！！`

## Goals

- Diagnose the persisted data for episode `340cacb9ed854bb18d50f2c69547bf03`, script `142`.
- Stop scene summaries from being accepted as production dialogue.
- Repair the current script, audio timeline, Timeline Spec, and storyboard support view so the page shows real character dialogue.
- Add focused regression coverage for the dialogue extraction and gate behavior.

## Changes

- Added quoted-dialogue extraction in `app/services/script_dialogue_extraction.py` so missing scene dialogue is rebuilt from quoted utterances before falling back to narration.
- Marked narration fallbacks as blocking in the script quality gate via `script_dialogue_fallback`.
- Reused the shared extraction helper from the mock script generator instead of keeping duplicate speaker parsing.
- Extended prose/stage cleanup to strip ASCII single-quoted dialogue from stage directions.
- Made `app.services.script` package exports lazy to avoid the `scene_audio_generator` import cycle seen during runtime repair.
- Added unit coverage for quote extraction, adjacent speaker resolution, fallback dialogue quality gate rejection, ASCII single-quote stage cleanup, and standalone scene audio generator import.
- Repaired live local data for script `142`:
  - `Script.dialogues`: rebuilt from 3 polluted entries to 11 character dialogue lines.
  - `episode.extra_metadata.audio_timeline`: regenerated to audio version `2`, 25 beats, duration `32.904s`.
  - `Timeline 67`: updated to version `2`, source audio version `2`.
  - Storyboard support: rebuilt to 11 timeline-aligned frames.

## Validation

- DB verification:
  - Script 142 now has 11 dialogue entries and no `fallback` dialogue.
  - Timeline 67 v2 has 11 `dialogue` clips and 11 `subtitle` clips.
  - Storyboard support has 11 frames with descriptions like `老拐, 又一个自动化完成了。` and `文闻, 我会留下，帮你加点人性化。`
  - Old polluted scene beat rows are soft-deleted history; active rows align with the regenerated timeline.
- Browser evidence:
  - Chrome DevTools transport was unavailable earlier (`127.0.0.1:9222` returned HTTP Not Found), so validation used Playwright with system Google Chrome as fallback.
  - Evidence stored under `artifacts/runs/dialogue-repair-20260609-121418/`.
  - `storyboard-dialogue-repair.json`: `presentCount=11`, `missing=[]`, `forbiddenPresent=[]`.
  - `storyboard-dialogue-repair.png`: captured the storyboard page at the target URL.
- Tests:
  - `cd ai-pic-backend && pytest tests/unit/services/test_script_missing_parts.py tests/unit/services/test_script_quality_gate_fallback_dialogue.py tests/unit/services/test_narrative_quality_gate.py tests/unit/services/audio/test_prose_dialogue_splitter.py tests/unit/services/audio/test_scene_audio_generator_import.py tests/unit/services/ai/test_scripts_generation_mixin.py tests/unit/services/ai/test_scripts_ai_manager_failures.py tests/unit/services/test_script_agent_react_fill.py tests/unit/services/test_script_quality_gate_runtime_failures.py tests/unit/services/script/test_script_service.py tests/unit/services/script/test_production_pipeline.py tests/unit/services/script/test_production_storyboard_timeline_import.py -v` passed: 48 passed.
  - File-level `black --check`, `isort --check-only --profile=black`, `ruff check`, and `git diff --check` passed for the touched Python files.
  - `python scripts/check_repo_docs.py` passed.
  - `python scripts/check_repo_contracts.py --mode diff ...` passed.
  - `cd ai-pic-backend && python run_tests.py quick` did not reach tests: dependency setup failed while building `pydantic-core==2.14.1` because local Rust/Cargo was not available on PATH.
- Runtime reload:
  - Restarted `ai-video-backend`, `ai-video-celery-worker`, and `ai-video-celery-beat`.
  - After restart, target page returned HTTP 200 and DB check still reported `dialogues=11`, `timeline_version=2`, `audio_version=2`, `frames=11`.

## Next Steps

- If committing, include this ledger with the code and tests.
- Full backend quick can be retried after installing Rust/Cargo or using a Python environment with a compatible prebuilt `pydantic-core` wheel.

## Linked Commits

- Pending.
