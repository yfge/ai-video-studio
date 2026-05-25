## User Prompt

参考 ../aiflay 接入 codex 形式调用的chat gpt ，同时也接入其中的chatgpt-img-2 模板

## Goals

- Reference `../aiflay`'s Codex/ChatGPT OAuth call shape.
- Add a backend `codex` text provider that uses local Codex CLI auth.
- Add `chatgpt-img-2` as an image model template alias routed to GPT Image 2.
- Keep changes scoped to provider/model configuration and tests.

## Changes

- Added Codex auth helpers that read and refresh `~/.codex/auth.json` without logging token values.
- Added `CodexProvider` for text generation through `https://chatgpt.com/backend-api/codex/responses` using streaming Responses API payloads.
- Split Codex payload/SSE parsing helpers out of the provider so the provider file stays under the repository service-file size limit.
- Wired `codex` into `AIService` through a small runtime registration helper; it auto-enables only when `CODEX_AUTH_PATH` is explicitly configured and the auth file exists.
- Added `CODEX_AUTH_PATH`, `CODEX_RESPONSES_URL`, and `CODEX_DEFAULT_MODEL` settings and example env entries.
- Added `chatgpt-img-2` as an OpenAI image alias/template that canonicalizes to `gpt-image-2`, with static model metadata and UI sizing parity.
- Added targeted unit tests for Codex payload/auth/SSE handling, token redaction, model alias parsing, image UI metadata, and static model listing.

## Validation

1. Local checks:

- `cd ai-pic-backend && python -m py_compile app/services/providers/codex_auth.py app/services/providers/codex_payload.py app/services/providers/codex_provider.py app/services/providers/codex_registration.py app/services/ai/service.py tests/unit/services/providers/test_codex_auth.py tests/unit/services/providers/test_codex_provider.py tests/unit/services/providers/test_codex_registration.py` -> passed.
- `cd ai-pic-backend && pytest tests/unit/services/providers/test_codex_auth.py tests/unit/services/providers/test_codex_provider.py tests/unit/services/providers/test_codex_registration.py tests/unit/test_model_utils.py tests/unit/services/providers/test_image_param_utils.py tests/unit/services/test_model_ui_image_gen_metadata.py tests/unit/test_model_listing.py -q` -> passed; 24 passed, 8 skipped, 37 warnings.
- `cd ai-pic-backend && python -m black --check <changed backend python files>` -> passed.
- `cd ai-pic-backend && python -m isort --profile=black --check-only <changed backend python files>` -> passed.
- `cd ai-pic-backend && python -m flake8 <changed backend python files> --max-line-length=88 --extend-ignore=E203,W503` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> passed.
- `git diff --check -- <changed files>` -> passed.
- `pre-commit run --all-files` -> failed outside this change's surface. Formatter hooks modified unrelated historical files and the backend quick gate failed while importing `tests.fixtures.client` because `app.services.script_quality.checks` does not export `check_cliffhanger`; the unrelated formatter mutations were reverted to preserve atomic commits.
- `BUILD_PUSH=false ./docker/build_prod_images.sh` -> passed for the whole dirty worktree before final commits; backend and frontend images were built locally without push with `IMAGE_TAG=f6cc4461`.
- `cd ai-pic-backend && python run_tests.py quick --no-setup` -> failed outside this change's surface: 7 failed, 1977 passed, 76 skipped, 20 deselected, 1651 warnings. Failures were script schema/regeneration, MySQL `127.0.0.1:13306` connection refused, API script generation 500, one order-dependent story fallback failure, and two prompt text expectation mismatches.
- Follow-up targeted failure replay: `pytest <7 failed tests> -q` -> 6 failed, 1 passed; `tests/test_story_generation_fallback.py::test_story_outline_falls_back_to_mock_when_ai_manager_unavailable` passed alone, leaving the same script/MySQL/prompt mismatch set.
- Earlier setup gate: `cd ai-pic-backend && python run_tests.py quick` failed before tests during dependency install because Python 3.13 resolved `pydantic==2.5.0` against `langchain-core==0.2.43`, which requires `pydantic>=2.7.4` for Python 3.12.4+.

2. Browser or MCP validation:

- Not run. This change is provider plumbing and model listing metadata; no live ChatGPT/Codex generation was executed in this pass.

3. Conflict signals and corrections:

- Initial assumption: `chatgpt-img-2` might require a separate image provider.
- Contradicting evidence: `../aiflay` only implements Codex text calls, while this repo already has GPT Image 2 image generation.
- Reproduction and fix: Implemented `codex` as a text-only provider and mapped `chatgpt-img-2` to the existing OpenAI GPT Image 2 path.
- Final verified state: Targeted unit tests cover the new provider behavior, token redaction, and alias propagation. The broad backend quick gate remains blocked by unrelated local/script/prompt failures listed above.

## Next Steps

- Run real-browser generation validation only when a live Codex/ChatGPT auth path is intended for the current environment.
- Resolve the existing script-generation, local MySQL, and storyboard prompt expectation failures before treating the broad backend quick gate as clean.

## Linked Commits

- Pending.
