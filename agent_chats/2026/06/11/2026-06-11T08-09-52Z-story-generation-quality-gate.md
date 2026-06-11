## User Prompt

修复 `http://localhost:8089/stories/68515e775b4143f0844b12bc5a1849b2` 暴露的故事质量下降问题，保证故事生成质量。

## Goals

- Confirm whether the issue was model selection or a broken generation/quality chain.
- Reject or repair story outlines that pass JSON schema but fail character-name or story-quality gates.
- Preserve provider/model/validation evidence in `agent_run` so future low-quality outputs are inspectable.
- Keep the change scoped to story-generation services and tests.

## Changes

- Added story-outline-specific quality gates so `StoryOutlineModel` fields (`synopsis`, `plot_structure`, `hook_plan`, `premise`, etc.) drive pacing and hook scoring.
- Made weak story-outline pacing and hook failures fatal for story generation payloads.
- Extracted story-outline character validation so generated `main_characters` are checked against the requested character names.
- Changed `StoryLangGraphAgent` to continue repair when character or story-quality validation fails, instead of returning the first schema-valid draft as `validated`.
- Prevented `StoryOutlineMixin` from falling through to weaker schema-only fallback after the quality-gated story agent fails to produce an accepted outline.
- Persisted story character and quality validation results into `Story.extra_metadata.agent_run` / task `agent_run` payloads via `build_agent_run`.
- Made `app.services.story` package export `StoryGenerationService` lazily so story submodule imports do not create an `ai_service` circular import.
- Added regression tests for story outline scoring, weak outline rejection, character-name drift repair, fallback bypass prevention, and validation audit persistence.

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest tests/unit/services/validators/test_story_quality_validator.py::TestStoryQualityValidator::test_validate_story_outline_uses_outline_fields tests/unit/services/validators/test_story_quality_validator.py::TestStoryQualityValidator::test_validate_story_outline_fails_weak_story tests/unit/services/test_story_agent_quality_gate.py::test_story_agent_repairs_when_outline_fails_quality_or_character_gate --no-cov -q` -> failed before implementation: outline fields scored 0, weak outline passed, story agent did not repair.
- `cd ai-pic-backend && pytest tests/unit/services/story/test_story_generation_utils.py::test_build_agent_run_keeps_story_validation_audit_fields --no-cov -q` -> failed before implementation: validation audit fields were omitted from `agent_run`.
- `cd ai-pic-backend && pytest tests/test_story_generation_fallback.py::test_story_outline_does_not_bypass_failed_quality_gated_agent --no-cov -q` -> failed before implementation after the fake fallback returned schema-valid weak content: fallback was accepted.
- `cd ai-pic-backend && pytest tests/unit/services/validators/test_story_quality_validator.py::TestStoryQualityValidator::test_validate_story_outline_uses_outline_fields tests/unit/services/validators/test_story_quality_validator.py::TestStoryQualityValidator::test_validate_story_outline_fails_weak_story tests/unit/services/test_story_agent_quality_gate.py::test_story_agent_repairs_when_outline_fails_quality_or_character_gate tests/unit/services/story/test_story_generation_utils.py::test_build_agent_run_keeps_story_validation_audit_fields tests/test_story_generation_fallback.py::test_story_outline_does_not_bypass_failed_quality_gated_agent --no-cov -q` -> passed after implementation.
- `cd ai-pic-backend && pytest tests/unit/services/validators/test_story_quality_validator.py tests/unit/services/test_story_agent_quality_gate.py tests/unit/services/story/test_story_generation_utils.py tests/test_story_generation_fallback.py --no-cov -q` -> passed: 37 tests.
- Refactored the outline quality checks out of oversized validator files after `python scripts/check_repo_contracts.py --mode diff ...` rejected `story_quality_validator.py`, `test_story_quality_validator.py`, and `story_agent.py` line counts.
- `cd ai-pic-backend && pytest tests/unit/services/story/test_story_outline_quality.py tests/unit/services/test_story_agent_quality_gate.py tests/unit/services/story/test_story_generation_utils.py tests/test_story_generation_fallback.py --no-cov -q` -> passed: 14 tests.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai/story_outline.py ai-pic-backend/app/services/story/__init__.py ai-pic-backend/app/services/story/story_generation_utils.py ai-pic-backend/app/services/story/story_outline_character_validation.py ai-pic-backend/app/services/story/story_outline_quality.py ai-pic-backend/app/services/story_agent.py ai-pic-backend/tests/test_story_generation_fallback.py ai-pic-backend/tests/unit/services/story/test_story_generation_utils.py ai-pic-backend/tests/unit/services/story/test_story_outline_quality.py ai-pic-backend/tests/unit/services/test_story_agent_quality_gate.py agent_chats/2026/06/11/2026-06-11T08-09-52Z-story-generation-quality-gate.md` -> passed.
- `git diff --check` -> passed.
- `cd ai-pic-backend && python run_tests.py quick` -> blocked during dependency setup: Python 3.13 dependency resolution conflicts because `langchain-core==0.2.43` requires `pydantic>=2.7.4` while the repo pins `pydantic==2.5.0`.
- `cd ai-pic-backend && python run_tests.py quick --no-setup` -> blocked during collection by existing missing symbols outside this change: `structured_script_score`, `STRUCTURED_SCORE_PASS`, and `_BEAT_CONTRACT_MAX_TOKENS`.

2. Browser or MCP validation:

- Not run. This change affects AI generation behavior, but a live generation would require the running backend/provider path to pick up the changed code and call the external model; no browser success is claimed.

3. Conflict signals and corrections:

- Initial question asked whether the model was wrong. Runtime evidence showed task `6042` explicitly used `deepseek:deepseek-v4-flash` and `agent_run.provider_used=deepseek`, so model routing was not the primary failure.
- The generated outline shortened `林晚_爽剧测试_01300519` to `林晚`; code inspection showed character validation only checked legacy `characters`, missing schema field `main_characters`.
- Manual validation of story `id=60` showed pacing/hook scores at 0 but `passed=true`; code inspection showed story-quality warnings were not fatal and outline fields were not used for scoring.

## Next Steps

- Restart the backend/Celery runtime before relying on this quality gate in localhost or production workers.
- Validate a local story-generation path after the running service has picked up the changed code and provider access is available.

## Linked Commits

- Pending.
