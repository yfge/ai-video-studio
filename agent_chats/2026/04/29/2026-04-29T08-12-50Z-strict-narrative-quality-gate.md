## User Prompt

PLEASE IMPLEMENT THIS PLAN:

# 剧集/剧本严格质量 Gate 计划

目标不是“绝对保证模型永远写得好”，而是保证低质量结果不能进入生产数据：生成结果必须经过结构、角色、连续性、时长和可制作性 Gate；最多自动修复 2 轮；仍未通过则任务失败且不创建剧集/剧本记录。第一阶段优先“生产可用”，不做前端和 DB schema 变更。

## Goals

- Add a shared narrative quality gate report for episode and script generation.
- Block malformed, incomplete, unknown-character, continuity, duration, and low-lint outputs before persistence.
- Allow at most two repair attempts and persist failure context into task `agent_run`.
- Ensure successful Episode/Script records store the `quality_gate` report.
- Keep the first-stage implementation backend-only, without API or schema changes.

## Changes

- Added `quality_gate_core.py`, `narrative_quality_gate.py`, `episode_quality_gate.py`, `script_quality_gate.py`, `script_quality_gate_checks.py`, and `quality_gate_repair.py`.
- Wired episode generation through strict final Gate checks in AI service, sync service, and async task persistence; async episode generation now gates the full result before creating visible Episode rows.
- Wired script generation, async generation, sync regeneration, and async regeneration through strict Gate checks before Script persistence or version creation.
- Added task failure audit context with `error.code = "quality_gate_failed"` and stable `quality_gate` report fields.
- Updated script text assembly and mock AI script output so deterministic lint can pass without real repair calls in tests.
- Added unit tests covering report aggregation, blocking checks, two-round repair success/failure, task failure context, and episode/script strict Gate behavior.

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/test_narrative_quality_gate.py -q` -> passed, 7 tests.
- `cd ai-pic-backend && pytest tests/unit/services/test_narrative_quality_gate.py tests/unit/services/test_narrative_context.py tests/unit/services/ai/test_episode_generation_strict.py tests/scripts/test_script_dialogue_fallback.py tests/scripts/test_script_story_structure_sync.py tests/test_api.py::TestScriptAPI::test_generate_script tests/unit/services/ai/test_scripts_generation_mixin.py tests/unit/services/test_script_agent_langgraph_early_exit.py tests/unit/services/test_script_agent_word_count.py tests/unit/test_episode_agent_callbacks.py -q` -> passed, 30 tests.
- `cd ai-pic-backend && pytest tests/integration/test_task_pipeline_agent_run_audit.py::test_story_episode_script_generate_async_persists_task_agent_run -q` -> passed.
- `cd ai-pic-backend && python -m ruff check ...` on changed backend files/tests -> passed.
- `python -m py_compile ...` on changed backend files/tests -> passed.
- `cd ai-pic-backend && python run_tests.py quick --no-setup` -> failed only on existing baseline failure `tests/unit/test_episode_step_outline_light.py::test_outline_missing_logline_triggers_repair`; result after this change: 1925 passed, 1 failed, 76 skipped, 20 deselected.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only) $(git ls-files --others --exclude-standard)` -> failed on pre-existing historical hotspot files touched by this narrow wiring change: oversized `scripts_legacy.py`, `episodes/async_tasks.py`, `script_generator.py`, `ai/episodes.py`, `episode_generation_service.py`; direct-query findings in `scripts_legacy.py`, `episodes/async_tasks.py`, and `episode_generation_service.py`; route-handler length in `scripts_legacy.py`.
- `pre-commit run --all-files` -> failed on broad repository baseline issues and modified unrelated historical files; unrelated hook rewrites were restored before staging. High-signal failures included existing all-file ruff/black/prettier drift, repo-wide backend pytest import failure during the temporary hook rewrite, and ledger enforcement for those unstaged hook rewrites.
- Post-cleanup staged-file checks: `cd ai-pic-backend && python -m ruff check ...`, `python -m py_compile ...`, and `pytest tests/unit/services/test_narrative_quality_gate.py tests/unit/services/test_narrative_context.py tests/unit/services/ai/test_scripts_generation_mixin.py tests/unit/services/test_script_agent_langgraph_early_exit.py tests/unit/services/test_script_agent_word_count.py tests/unit/test_episode_agent_callbacks.py -q` -> passed, 25 tests.

## Next Steps

- Fix the existing episode step-outline expectation in a separate change if the team wants quick to become fully green.
- Plan a separate extraction/refactor for the historical script/episode endpoint hotspots so future contract diff checks can pass when these paths need small behavior changes.
- Consider adding browser-level evidence only when a frontend-visible task page workflow changes; this change is backend-only.

## Linked Commits

- None yet.
