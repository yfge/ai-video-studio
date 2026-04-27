---
id: 2026-04-27T10-50-04Z-audio-concat-normalization
date: "2026-04-27T10:50:04Z"
participants: [user, codex]
models: [gpt-5]
tags: [backend, audio, tests]
related_paths:
  - ai-pic-backend/app/services/audio/audio_generator.py
  - ai-pic-backend/app/services/audio/audio_emotions.py
  - ai-pic-backend/tests/unit/services/audio/test_audio_generator.py
  - ai-pic-backend/tests/unit/services/audio/test_audio_generator_concat.py
  - ai-pic-backend/tests/unit/services/audio/test_audio_emotions.py
summary: "Normalized MP3 concatenation through WAV intermediates and split audio utility tests under file-size limits."
---

## User Prompt

分批提交工作区内其他改动

## Goals

- Preserve the workspace audio concatenation fix while making the touched utility file pass repository size contracts.
- Keep `ensure_oss_configured()` usable both with an explicit service and as a no-argument singleton guard.
- Update focused audio utility tests without leaving oversized test files.

## Changes

- Added `normalize_wav()` and changed `concat_mp3s()` to decode each MP3 to normalized mono PCM WAV, concatenate WAVs, then encode one final MP3.
- Moved TTS emotion labels and normalization into `audio_emotions.py` while re-exporting them from `audio_generator.py`.
- Kept `ensure_oss_configured(None)` as an explicit failure and added no-argument singleton lookup for new callers.
- Split audio generator tests into focused emotion and concat test modules; updated MP3 concat coverage for the normalized WAV workflow and empty input failure.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/audio/audio_generator.py ai-pic-backend/app/services/audio/audio_emotions.py ai-pic-backend/tests/unit/services/audio/test_audio_generator.py ai-pic-backend/tests/unit/services/audio/test_audio_generator_concat.py ai-pic-backend/tests/unit/services/audio/test_audio_emotions.py` -> passed.
- `cd ai-pic-backend && python -m ruff check <changed audio utility files and tests>` -> passed.
- `cd ai-pic-backend && python -m black --check <changed audio utility files and tests>` -> passed.
- `cd ai-pic-backend && python -m isort --profile=black --check-only <changed audio utility files and tests>` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed audio utility files and tests>` -> passed: `[check_repo_contracts] ok (diff)`.
- `python scripts/check_repo_docs.py` -> passed: `[check_repo_docs] ok`.
- `cd ai-pic-backend && pytest tests/unit/services/audio/test_audio_generator.py tests/unit/services/audio/test_audio_generator_concat.py tests/unit/services/audio/test_audio_emotions.py tests/unit/services/audio/test_timeline_processor.py -q` -> passed: `57 passed, 25 warnings`.
- `cd ai-pic-backend && python run_tests.py quick` -> failed during dependency installation before tests ran. Pip reported the existing Python 3.13 resolver conflict: repository-pinned `pydantic==2.5.0` conflicts with `langchain-core==0.2.43`, which requires `pydantic>=2.7.4` for `python_full_version >= "3.12.4"`.

2. Browser or MCP validation:

- Not run. This change is backend audio utility behavior with no direct browser path.

3. Conflict signals and corrections:

- Initial issue: direct MP3 concat/copy can fail on some ffmpeg builds when producing episode-level audio.
- Correction: decode source MP3 files to normalized WAV, concatenate WAV, and encode final MP3 once.

## Next Steps

- Re-run `python run_tests.py quick` in an environment whose Python/dependency pins resolve cleanly.

## Linked Commits

- This commit: `fix(backend): normalize mp3 audio concatenation`.
