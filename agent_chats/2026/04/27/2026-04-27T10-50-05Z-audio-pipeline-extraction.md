---
id: 2026-04-27T10-50-05Z-audio-pipeline-extraction
date: "2026-04-27T10:50:05Z"
participants: [user, codex]
models: [gpt-5]
tags: [backend, audio, refactor]
related_paths:
  - ai-pic-backend/app/repositories/audio_timeline_repository.py
  - ai-pic-backend/app/services/audio/episode_audio_builder.py
  - ai-pic-backend/app/services/audio/episode_timeline_beats.py
  - ai-pic-backend/app/services/audio/scene_audio_assembler.py
  - ai-pic-backend/app/services/audio/scene_audio_generator.py
  - ai-pic-backend/app/services/audio/scene_audio_persistence.py
  - ai-pic-backend/app/services/audio/scene_fallback_tts.py
  - ai-pic-backend/app/services/audio/scene_tts_phase.py
  - ai-pic-backend/app/services/audio/storyboard_from_timeline.py
  - ai-pic-backend/app/services/audio/storyboard_timeline_helpers.py
summary: "Split scene and episode audio timeline generation into contract-sized helper modules with repository-owned database reads."
---

## User Prompt

分批提交工作区内其他改动

## Goals

- Preserve the workspace audio pipeline extraction as focused modules.
- Keep all new backend service files under repository file-size limits.
- Move new SQLAlchemy reads out of service modules and into a repository.

## Changes

- Added `audio_timeline_repository.py` for script scene loading, scene beat loading, and active scene beat lookups.
- Split episode timeline beat construction into `episode_timeline_beats.py` and episode audio assembly into `episode_audio_builder.py`.
- Split scene dialogue audio generation into TTS phase, timing orchestration, fallback TTS, assembly, and persistence helpers.
- Split audio-timeline storyboard frame generation helpers out of `storyboard_from_timeline.py`.
- Removed direct `.query(...)` usage from the new service modules and kept all touched files below the configured line-count limits.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/audio/episode_audio_builder.py ai-pic-backend/app/services/audio/episode_timeline_beats.py ai-pic-backend/app/services/audio/scene_audio_assembler.py ai-pic-backend/app/services/audio/scene_audio_generator.py ai-pic-backend/app/services/audio/scene_audio_persistence.py ai-pic-backend/app/services/audio/scene_fallback_tts.py ai-pic-backend/app/services/audio/scene_tts_phase.py ai-pic-backend/app/services/audio/storyboard_from_timeline.py ai-pic-backend/app/services/audio/storyboard_timeline_helpers.py ai-pic-backend/app/repositories/audio_timeline_repository.py` -> passed.
- `cd ai-pic-backend && python -m ruff check <new audio pipeline files>` -> passed.
- `cd ai-pic-backend && python -m black --check <new audio pipeline files>` -> passed.
- `cd ai-pic-backend && python -m isort --profile=black --check-only <new audio pipeline files>` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <new audio pipeline files>` -> passed: `[check_repo_contracts] ok (diff)`.
- `python scripts/check_repo_docs.py` -> passed: `[check_repo_docs] ok`.
- `cd ai-pic-backend && pytest tests/unit/services/audio/test_audio_generator.py tests/unit/services/audio/test_audio_generator_concat.py tests/unit/services/audio/test_audio_emotions.py tests/unit/services/audio/test_timeline_processor.py -q` -> passed: `57 passed, 25 warnings`.
- `cd ai-pic-backend && python run_tests.py quick` -> failed during dependency installation before tests ran. Pip reported the existing Python 3.13 resolver conflict: repository-pinned `pydantic==2.5.0` conflicts with `langchain-core==0.2.43`, which requires `pydantic>=2.7.4` for `python_full_version >= "3.12.4"`.

2. Browser or MCP validation:

- Not run. These are backend service extraction modules and are not wired to a new frontend flow in this commit.

3. Conflict signals and corrections:

- Contract check initially failed on oversized new service files and direct `db.query(...)` usage.
- Correction: split large modules further and moved scene/beat queries into `audio_timeline_repository.py`.
- Final contract state: `python scripts/check_repo_contracts.py --mode diff <new audio pipeline files>` passed.

## Next Steps

- Wire these split modules into active endpoints in a separate change if the project decides to retire the legacy `dialogue_audio_service.py` entrypoint.
- Re-run `python run_tests.py quick` in an environment whose Python/dependency pins resolve cleanly.

## Linked Commits

- This commit: `refactor(backend): extract audio timeline pipeline modules`.
