---
id: 2026-04-27T09-24-05Z-deepseek-v4-provider
date: 2026-04-27T09:24:05Z
participants: [user, codex]
models: [gpt-5]
tags: [backend, provider, deepseek, text-generation]
related_paths:
  - ai-pic-backend/app/services/providers/deepseek_provider.py
  - ai-pic-backend/app/services/providers/deepseek_models.py
  - ai-pic-backend/app/services/providers/deepseek_request.py
  - ai-pic-backend/app/services/providers/deepseek_response.py
  - ai-pic-backend/app/services/providers/deepseek_text.py
  - ai-pic-backend/tests/unit/test_deepseek_provider_v4.py
summary: "Integrated DeepSeek V4 Pro and V4 Flash model metadata and request handling."
---

## User Prompt

接入最新的deepseek v4

## Goals

- Verify the current official DeepSeek V4 API model IDs before editing.
- Add DeepSeek V4 Pro and V4 Flash to the provider fallback model list.
- Move DeepSeek provider code back under repository file-size limits.
- Keep legacy `deepseek-chat` and `deepseek-reasoner` visible as deprecated compatibility names.
- Preserve streaming behavior and non-stream fallback while adding V4 thinking-mode request handling.

## Changes

- Confirmed from official DeepSeek docs that DeepSeek V4 Preview was released on 2026-04-24 with API model IDs `deepseek-v4-pro` and `deepseek-v4-flash`.
  - Official release note: https://api-docs.deepseek.com/news/news260424
  - Models/pricing page: https://api-docs.deepseek.com/quick_start/pricing
  - First API call page: https://api-docs.deepseek.com/
- Split the previous oversized `deepseek_provider.py` into focused modules:
  - `deepseek_models.py` for model IDs, static fallback metadata, alias normalization, and capability inference.
  - `deepseek_request.py` for OpenAI-compatible chat request construction and thinking-mode handling.
  - `deepseek_response.py` for stream and response parsing.
  - `deepseek_text.py` for text generation orchestration.
- Updated DeepSeek defaults:
  - Text generation defaults to `deepseek-v4-flash`.
  - Code and math helper methods default to `deepseek-v4-pro`.
  - `deepseek-v4` aliases to `deepseek-v4-pro`.
- Kept compatibility metadata for `deepseek-chat` and `deepseek-reasoner`, including the documented 2026-07-24 retirement date.
- Normalized the repository's previous `https://api.deepseek.com/v1` config default inside the provider to the official `https://api.deepseek.com` base URL without touching the legacy `ai/base.py` config file.
- Added focused unit coverage in `tests/unit/test_deepseek_provider_v4.py`.

## Validation

1. Local checks:

- `cd ai-pic-backend && python -m black --check app/services/providers/deepseek_provider.py app/services/providers/deepseek_models.py app/services/providers/deepseek_request.py app/services/providers/deepseek_response.py app/services/providers/deepseek_text.py tests/unit/test_deepseek_provider_v4.py` -> passed.
- `cd ai-pic-backend && python -m ruff check app/services/providers/deepseek_provider.py app/services/providers/deepseek_models.py app/services/providers/deepseek_request.py app/services/providers/deepseek_response.py app/services/providers/deepseek_text.py tests/unit/test_deepseek_provider_v4.py` -> passed.
- `cd ai-pic-backend && pytest tests/unit/test_deepseek_provider_v4.py tests/unit/test_model_listing.py tests/unit/test_model_utils.py tests/unit/test_ai_providers_http_exception_passthrough.py -v` -> passed after final formatting: 14 passed, 8 skipped.
- `python -m compileall ai-pic-backend/app/services/providers ai-pic-backend/app/services/ai/base.py` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/providers/deepseek_provider.py ai-pic-backend/app/services/providers/deepseek_models.py ai-pic-backend/app/services/providers/deepseek_request.py ai-pic-backend/app/services/providers/deepseek_response.py ai-pic-backend/app/services/providers/deepseek_text.py ai-pic-backend/tests/unit/test_deepseek_provider_v4.py` -> passed.
- `pre-commit run --files ai-pic-backend/app/services/providers/deepseek_provider.py ai-pic-backend/app/services/providers/deepseek_models.py ai-pic-backend/app/services/providers/deepseek_request.py ai-pic-backend/app/services/providers/deepseek_response.py ai-pic-backend/app/services/providers/deepseek_text.py ai-pic-backend/tests/unit/test_deepseek_provider_v4.py agent_chats/2026/04/27/2026-04-27T09-24-05Z-deepseek-v4-provider.md` -> non-pytest hooks passed: merge conflict, whitespace, EOF, ruff, black after formatting, isort, prettier, repository docs, repository contracts, and ledger enforcement. `backend-pytest` failed outside this change's DeepSeek files: `tests/unit/services/audio/test_audio_generator.py::TestEnsureOSSConfigured::test_raises_when_none`, `tests/unit/services/audio/test_audio_generator.py::TestConcatMp3s::test_concat_mp3s`, `tests/unit/services/image/test_image_generation_service.py::TestGenerateVirtualIPImage::test_generate_with_dalle`, and `tests/unit/services/image/test_image_providers.py::TestGenerateWithOpenAIDalle::test_generate_normalizes_style`. The working tree had existing unrelated audio/image/openai modifications that this change did not touch.

2. Browser or MCP validation:

- Not run. This change affects AI generation, but no Chrome DevTools/browser MCP tool was available in this session (`tool_search` for Chrome/browser DevTools returned no tools). No credentialed DeepSeek generation path was started from the UI.

3. Conflict signals and corrections:

- Initial assumption: update the central provider config base URL directly to DeepSeek's official `https://api.deepseek.com`.
- Contradicting evidence: `scripts/check_repo_contracts.py` rejected `ai-pic-backend/app/services/ai/base.py` as a legacy reference.
- Correction: restored that file and normalized the old `/v1` URL inside the DeepSeek provider instead.
- Final verified state: DeepSeek V4 defaults and request construction are covered by unit tests, and touched provider files are within file-size limits.

## Next Steps

- Run a real browser generation path with DeepSeek V4 when Chrome DevTools MCP and app credentials are available.
- Decide whether to hide deprecated `deepseek-chat` / `deepseek-reasoner` from the UI closer to the documented 2026-07-24 retirement date.

## Linked Commits

- This commit: `feat(backend): add deepseek v4 provider support`.
