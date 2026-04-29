## User Prompt

PLEASE IMPLEMENT THIS PLAN:

# LangGraph 链路第一批实现计划

实现第一批低风险修复，目标是让“剧集 -> 剧本”链路的现有校验真正生效：默认启用剧本时长 REACT、把 continuity ledger 传入剧本图、统一故事角色字段读取。暂不重构大文件、不改前端、不改数据库 schema。

## Goals

- 默认启用剧本生成中的 episode duration 驱动场景预算和 REACT 校验。
- 将 story continuity ledger 传入 ScriptLangGraphAgent。
- 统一 Episode/Script agent 对 story 角色字段的读取。
- 让 ScriptLangGraphAgent 的未知 speaker 结果包含 `unknown_names`。
- 保持改动符合仓库合同，不扩大已知热点文件。

## Changes

- Added `app/services/narrative_context.py` with `extract_story_characters(...)` supporting `characters`, `character_profiles`, and `main_characters`.
- Updated script generation to pass `duration_minutes=None` when no external scene budgets are supplied, and to pass `continuity_ledger` into the LangGraph script path.
- Split script text assembly into `app/services/ai/script_text.py` and reduced `app/services/ai/scripts.py` below the service file-size limit.
- Split episode character/quality validation into `app/services/episode_agent_validation.py` and reduced `app/services/episode_agent.py` below the service file-size limit.
- Updated ScriptLangGraphAgent to use the shared story character extractor and return `unknown_names` for unknown dialogue speakers.
- Added targeted unit coverage for script generation kwargs, character extraction, Episode/Script agent character validation, and unknown speaker reporting.

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest tests/unit/services/ai/test_scripts_generation_mixin.py tests/unit/services/test_narrative_context.py tests/unit/test_episode_agent_callbacks.py tests/unit/services/test_script_agent_langgraph_early_exit.py tests/unit/services/test_script_agent_word_count.py -v` -> passed, 18 tests.
- `python -m ruff check ai-pic-backend/app/services/ai/scripts.py ai-pic-backend/app/services/ai/script_text.py ai-pic-backend/app/services/episode_agent.py ai-pic-backend/app/services/episode_agent_validation.py ai-pic-backend/app/services/narrative_context.py ai-pic-backend/app/services/script_agent.py ai-pic-backend/tests/unit/services/ai/test_scripts_generation_mixin.py ai-pic-backend/tests/unit/services/test_script_agent_langgraph_early_exit.py ai-pic-backend/tests/unit/services/test_script_agent_word_count.py ai-pic-backend/tests/unit/services/test_narrative_context.py ai-pic-backend/tests/unit/test_episode_agent_callbacks.py` -> passed.
- `cd ai-pic-backend && black --check app/services/ai/scripts.py app/services/ai/script_text.py app/services/episode_agent.py app/services/episode_agent_validation.py app/services/narrative_context.py tests/unit/services/ai/test_scripts_generation_mixin.py tests/unit/services/test_script_agent_langgraph_early_exit.py tests/unit/services/test_script_agent_word_count.py tests/unit/services/test_narrative_context.py tests/unit/test_episode_agent_callbacks.py && isort --profile=black --check-only app/services/ai/scripts.py app/services/ai/script_text.py app/services/episode_agent.py app/services/episode_agent_validation.py app/services/narrative_context.py tests/unit/services/ai/test_scripts_generation_mixin.py tests/unit/services/test_script_agent_langgraph_early_exit.py tests/unit/services/test_script_agent_word_count.py tests/unit/services/test_narrative_context.py tests/unit/test_episode_agent_callbacks.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai/scripts.py ai-pic-backend/app/services/ai/script_text.py ai-pic-backend/app/services/episode_agent.py ai-pic-backend/app/services/episode_agent_validation.py ai-pic-backend/app/services/narrative_context.py ai-pic-backend/app/services/script_agent.py ai-pic-backend/tests/unit/services/ai/test_scripts_generation_mixin.py ai-pic-backend/tests/unit/services/test_script_agent_langgraph_early_exit.py ai-pic-backend/tests/unit/services/test_script_agent_word_count.py ai-pic-backend/tests/unit/services/test_narrative_context.py ai-pic-backend/tests/unit/test_episode_agent_callbacks.py` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `cd ai-pic-backend && python run_tests.py quick` -> failed during dependency setup before tests: pip dependency resolution conflict on Python 3.13 (`pydantic==2.5.0` vs `langchain-core==0.2.43` requiring `pydantic>=2.7.4`).
- `cd ai-pic-backend && python run_tests.py quick --no-setup` -> test body ran, but failed on the existing unrelated case `tests/unit/test_episode_step_outline_light.py::test_outline_missing_logline_triggers_repair`: expected fake generated episode summary `S`, but current validation falls back to the repaired outline summary `修复后` because the fake episode payload lacks required scene content. Result: 1918 passed, 1 failed, 76 skipped, 20 deselected.

2. Browser or MCP validation:

- Not run. This backend-only change affects generation internals and was covered by service/unit tests; no frontend/browser path was changed.

3. Conflict signals and corrections:

- Initial assumption: `python run_tests.py quick` would reach pytest.
- Contradicting evidence: runner failed during `pip install -r requirements-test.txt` dependency resolution.
- Reproduction and fix: reran `python run_tests.py quick --no-setup` to validate the pytest body against the existing environment; documented the unrelated baseline failure.
- Final verified state: targeted tests and repo contract/doc/format checks pass; full quick remains blocked by environment setup plus unrelated existing test expectations.

## Next Steps

- Optionally fix the two existing quick-suite failures in a separate change.
- Consider updating the backend test environment pins for Python 3.13 compatibility.

## Linked Commits

- None yet.
