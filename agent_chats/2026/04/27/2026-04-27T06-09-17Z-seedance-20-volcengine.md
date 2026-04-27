---
id: 2026-04-27T06-09-17Z-seedance-20-volcengine
date: 2026-04-27T06:09:17Z
participants: [user, codex]
models: [gpt-5]
tags: [backend, provider, volcengine, seedance, video]
related_paths:
  - ai-pic-backend/app/services/providers/volcengine_provider/models.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video_tasks.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video_models.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video_request.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video_request_params.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video_response.py
  - ai-pic-backend/tests/unit/test_volcengine_provider_video.py
summary: "Integrated Volcengine Seedance 2.0 model metadata and Ark video request construction."
---

## User Prompt

接入 seedance-2.0 已经有了相关的文档

## Goals

- Add Seedance 2.0 / 2.0 Fast to the Volcengine video model registry.
- Align Volcengine Ark video request payloads with `docs/api/volcengine-video-2.0.md`, especially top-level generation params and multimodal `content` roles.
- Keep provider files within repository size limits after touching them.
- Add targeted unit coverage for model metadata, aliases, request construction, and remote model inference.

## Changes

- Split Volcengine video model definitions into `video_models.py` and added Seedance 2.0 standard/Fast plus Seedance 1.5 Pro metadata.
- Reworked video request building into `video_request.py` and `video_request_params.py`.
  - Uses top-level `resolution`, `ratio`, `duration`, `watermark`, `seed`, `generate_audio`, etc. instead of prompt suffix flags for the provider request.
  - Maps `seedance-2.0`, `seedance-2.0-i2v`, `seedance-2.0-fast`, and related aliases to the Ark model IDs.
  - Converts multimodal references to `content` items with `reference_image`, `reference_video`, and `reference_audio` roles.
  - Keeps first-frame / last-frame mode separate from multimodal reference mode per the Volcengine docs.
  - Skips unsupported Seedance 2.0 fields such as `camera_fixed` and `service_tier=flex`.
- Shared Volcengine task response parsing in `video_response.py`.
- Reduced touched provider files below the configured service file-size limit.
- Added `tests/unit/test_volcengine_provider_video.py`.

## Validation

1. Local checks:

- `python -m compileall ai-pic-backend/app/services/providers/volcengine_provider` -> passed; all touched provider modules compile.
- `cd ai-pic-backend && pytest tests/unit/test_volcengine_provider_video.py -v` -> passed: 6 passed.
- `cd ai-pic-backend && pytest tests/unit/test_volcengine_provider_video.py tests/unit/test_model_listing.py tests/unit/services/video/test_video_ui_utils.py -v` -> passed after final formatting: 25 passed, 2 skipped. Skips were existing OpenAI UI utility skips.
- `cd ai-pic-backend && python -m black --check app/services/providers/volcengine_provider/models.py app/services/providers/volcengine_provider/video.py app/services/providers/volcengine_provider/video_tasks.py app/services/providers/volcengine_provider/video_models.py app/services/providers/volcengine_provider/video_request.py app/services/providers/volcengine_provider/video_request_params.py app/services/providers/volcengine_provider/video_response.py tests/unit/test_volcengine_provider_video.py` -> passed.
- `cd ai-pic-backend && python -m ruff check app/services/providers/volcengine_provider/models.py app/services/providers/volcengine_provider/video.py app/services/providers/volcengine_provider/video_tasks.py app/services/providers/volcengine_provider/video_models.py app/services/providers/volcengine_provider/video_request.py app/services/providers/volcengine_provider/video_request_params.py app/services/providers/volcengine_provider/video_response.py tests/unit/test_volcengine_provider_video.py` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/providers/volcengine_provider/models.py ai-pic-backend/app/services/providers/volcengine_provider/video.py ai-pic-backend/app/services/providers/volcengine_provider/video_tasks.py ai-pic-backend/app/services/providers/volcengine_provider/video_models.py ai-pic-backend/app/services/providers/volcengine_provider/video_request.py ai-pic-backend/app/services/providers/volcengine_provider/video_request_params.py ai-pic-backend/app/services/providers/volcengine_provider/video_response.py ai-pic-backend/tests/unit/test_volcengine_provider_video.py` -> passed.
- `cd ai-pic-backend && python run_tests.py quick` -> failed before running tests during dependency setup. Pip reported a resolver conflict on Python 3.13: repository-pinned `pydantic==2.5.0` conflicts with `langchain-core==0.2.43`, which requires `pydantic>=2.7.4` for `python_full_version >= "3.12.4"`.
- `pre-commit run --files ai-pic-backend/app/services/providers/volcengine_provider/models.py ai-pic-backend/app/services/providers/volcengine_provider/video.py ai-pic-backend/app/services/providers/volcengine_provider/video_tasks.py ai-pic-backend/app/services/providers/volcengine_provider/video_models.py ai-pic-backend/app/services/providers/volcengine_provider/video_request.py ai-pic-backend/app/services/providers/volcengine_provider/video_request_params.py ai-pic-backend/app/services/providers/volcengine_provider/video_response.py ai-pic-backend/tests/unit/test_volcengine_provider_video.py agent_chats/2026/04/27/2026-04-27T06-09-17Z-seedance-20-volcengine.md` -> non-pytest hooks passed: merge conflict, whitespace, EOF, ruff, black, isort, prettier, repository docs, repository contracts, and ledger enforcement. `backend-pytest` failed in the pre-existing dirty audio area: `tests/unit/services/audio/test_audio_generator.py::TestEnsureOSSConfigured::test_raises_when_none` and `tests/unit/services/audio/test_audio_generator.py::TestConcatMp3s::test_concat_mp3s`. The working tree already had an unstaged modification in `ai-pic-backend/app/services/audio/audio_generator.py`, which this change did not touch.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> passed; backend and frontend production images built locally without pushing. The frontend Docker build reported existing `npm audit` vulnerabilities.

2. Browser or MCP validation:

- Not run. This change affects provider payload behavior, but Chrome DevTools MCP was not available in this session (`tool_search` for Chrome/browser DevTools returned no tools). No local app stack or Volcengine credentialed generation path was started.

3. Conflict signals and corrections:

- Initial assumption: existing Volcengine video request passthrough could carry new 2.0 fields.
- Contradicting evidence: `reference_images` would be sent as an unsupported top-level field instead of a `content` item with `role=reference_image`.
- Correction: introduced a dedicated request builder that maps first/last frame and multimodal reference modes to the documented Ark `content` shape, with unit assertions on the outgoing payload.

## Next Steps

- Run a real browser storyboard/video submission path when the local stack, Chrome DevTools transport, and Volcengine credentials are available.
- Re-run `python run_tests.py quick` in a Python version/dependency environment that satisfies the repository pins.

## Linked Commits

- This commit: `feat(backend): add seedance 2.0 volcengine video support`.
