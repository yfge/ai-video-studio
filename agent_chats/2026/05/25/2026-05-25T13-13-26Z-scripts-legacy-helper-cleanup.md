## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue the main-chain readiness plan with another atomic backend cleanup.
- Reduce `scripts_legacy.py` duplication without changing runtime route behavior.
- Keep script generation API validation passing through the current quality gate.

## Changes

- Moved the shared script task title formatter into
  `app.services.script.task_titles`.
- Updated `scripts_legacy.py` and split audio/timeline pipeline endpoint helpers
  to use the shared formatter.
- Removed unused URL, UUID, and datetime helpers from `scripts_legacy.py`.
- Added `tests.fixtures.mock_ai_text_payloads` so the backend mock AI service can
  return schema-matched responses for script cliffhanger judgement and script
  quality-gate repair prompts without growing the fixture past contract limits.
- Replaced a touched direct script access query in `audio_pipeline_utils.py` with
  `ScriptRepository.get_with_relations`.
- Updated `tasks.md` and the active commercial readiness plan with the completed
  cleanup slice.

## Validation

- `python -m py_compile ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts/audio_pipeline_utils.py ai-pic-backend/app/api/v1/endpoints/scripts/audio_storyboard.py ai-pic-backend/app/api/v1/endpoints/scripts/audio_timeline.py ai-pic-backend/app/api/v1/endpoints/scripts/dialogue_audio.py ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py ai-pic-backend/app/services/script/task_titles.py ai-pic-backend/tests/fixtures/mock_ai_service.py ai-pic-backend/tests/fixtures/mock_ai_text_payloads.py`
- `cd ai-pic-backend && pytest tests/test_api.py::TestScriptAPI::test_generate_script -q`
  - Passed: 1 test.
- `cd ai-pic-backend && pytest tests/test_api.py -q`
  - Passed: 28 tests, 1 skipped.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts/audio_pipeline_utils.py ai-pic-backend/app/api/v1/endpoints/scripts/audio_storyboard.py ai-pic-backend/app/api/v1/endpoints/scripts/audio_timeline.py ai-pic-backend/app/api/v1/endpoints/scripts/dialogue_audio.py ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py ai-pic-backend/app/services/script/task_titles.py ai-pic-backend/tests/fixtures/mock_ai_service.py ai-pic-backend/tests/fixtures/mock_ai_text_payloads.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T13-13-26Z-scripts-legacy-helper-cleanup.md`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts/audio_pipeline_utils.py ai-pic-backend/app/api/v1/endpoints/scripts/audio_storyboard.py ai-pic-backend/app/api/v1/endpoints/scripts/audio_timeline.py ai-pic-backend/app/api/v1/endpoints/scripts/dialogue_audio.py ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py ai-pic-backend/app/services/script/task_titles.py ai-pic-backend/tests/fixtures/mock_ai_service.py ai-pic-backend/tests/fixtures/mock_ai_text_payloads.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T13-13-26Z-scripts-legacy-helper-cleanup.md`
  - Passed after isort reformatted imports; backend quick gate passed inside the hook.

## Next Steps

- Continue reducing legacy risk around `scripts_legacy.py`, especially moving
  production user paths off the legacy router.
- Keep production sample validation in 2D/3D cartoon style to avoid provider
  live-action human restrictions dominating the result.

## Linked Commits

Pending
