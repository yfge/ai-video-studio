## User Prompt

PLEASE IMPLEMENT THIS PLAN:

修复“生成剧本后自动跑的 production 时间轴链路”不复用一键 Timeline 主链时长控制的问题。自动 production 链路应走 duration-control 主链，不再走逐场景短音频占位逻辑；不回写历史数据。

## Goals

- Add a backend service-level shared runner for dialogue audio, episode audio timeline, Timeline Spec import, and Timeline shot plan.
- Keep the public manual one-click Timeline API unchanged while routing its worker through the shared runner.
- Route production auto timeline generation through the shared runner with duration control enabled and audio/timeline overwrite enabled.
- Preserve existing storyboard placeholder, hook annotation, and storyboard image queue behavior.
- Add focused tests proving automatic production uses the shared duration-control path and manual one-click Timeline still imports Timeline Spec and shot-plan metadata.

## Changes

- Added `app/services/timeline_pipeline_runner.py` with `run_timeline_main_chain`.
- Updated the timeline pipeline worker to delegate the main audio/timeline/shot-plan chain to the shared runner.
- Updated production storyboard auto timeline generation to use the shared runner with `use_duration_control=True`, `overwrite_audio=True`, and `overwrite_timeline=True`.
- Updated production and timeline pipeline tests to patch the new runner boundary or runner internals instead of endpoint-local functions.

## Validation

- Red check first: `cd ai-pic-backend && .venv/bin/python -m pytest tests/unit/services/script/test_production_storyboard_timeline_import.py -q`
  - Expected failure observed before implementation: old production path called `generate_scene_dialogue_audio`.
- Targeted backend tests: `cd ai-pic-backend && .venv/bin/python -m pytest tests/unit/services/script/test_production_storyboard_timeline_import.py tests/integration/test_timeline_pipeline_import_api.py tests/integration/test_duration_control_api.py tests/integration/test_timeline_pipeline_errors.py -v`
  - Passed: 7 passed. Re-run after formatting also passed: 7 passed.
- Repo docs: `python scripts/check_repo_docs.py`
  - Passed.
- Repo contracts: `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/timeline_pipeline_runner.py ai-pic-backend/app/services/script/production_storyboard.py ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py ai-pic-backend/tests/unit/services/script/test_production_storyboard_timeline_import.py ai-pic-backend/tests/integration/test_timeline_pipeline_import_api.py ai-pic-backend/tests/integration/test_timeline_pipeline_errors.py agent_chats/2026/06/11/2026-06-11T13-03-11Z-production-timeline-main-chain.md`
  - Passed.
- Whitespace: `git diff --check`
  - Passed.
- Formatting: `cd ai-pic-backend && .venv/bin/black --check app/services/timeline_pipeline_runner.py app/services/script/production_storyboard.py app/api/v1/endpoints/scripts/timeline_pipeline.py tests/unit/services/script/test_production_storyboard_timeline_import.py tests/integration/test_timeline_pipeline_import_api.py tests/integration/test_timeline_pipeline_errors.py && .venv/bin/isort --profile=black --check-only app/services/timeline_pipeline_runner.py app/services/script/production_storyboard.py app/api/v1/endpoints/scripts/timeline_pipeline.py tests/unit/services/script/test_production_storyboard_timeline_import.py tests/integration/test_timeline_pipeline_import_api.py tests/integration/test_timeline_pipeline_errors.py`
  - Passed.
- Backend quick regression: `cd ai-pic-backend && PATH="$PWD/.venv/bin:$PATH" .venv/bin/python run_tests.py quick`
  - Blocked during broader pytest collection by existing script/provider import errors. First confirmed error with `pytest tests/ -m 'not slow' -q --disable-warnings --maxfail=1`: `ImportError: cannot import name 'structured_script_score' from 'scripts.harness.production_quality_script'`.

## Next Steps

- Investigate the existing production quality script/provider collection errors before treating `run_tests.py quick` as a clean full-regression gate.

## Linked Commits

- This commit.
