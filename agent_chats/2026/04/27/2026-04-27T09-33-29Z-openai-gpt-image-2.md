## User Prompt

接入最新的openai img-gen-2

## Goals

- Verify the current official OpenAI image model name from OpenAI documentation.
- Integrate the latest OpenAI image generation model while accepting the user-facing `img-gen-2` alias.
- Preserve existing DALL-E 2 and DALL-E 3 behavior.
- Expose GPT Image 2 capabilities, sizes, and reference-image support through backend provider metadata and normalization.
- Add focused tests for model aliasing, request payloads, reference-image edits, UI metadata, and size validation.

## Changes

- Added `gpt-image-2` as the default OpenAI image model and canonical target for `img-gen-2`, `image-gen-2`, and `gpt-img-2` aliases.
- Updated model/provider inference helpers so OpenAI image models route through the OpenAI provider instead of fallback paths.
- Added GPT Image 2 metadata, capabilities, size options, custom-size validation, and UI reference-image support.
- Updated OpenAI image generation calls to use GPT Image compatible request parameters, including `quality=auto`, no DALL-E-only `style` or `response_format`, and base64 response extraction.
- Added GPT Image edit support through `/v1/images/edits` for reference-image and image-to-image flows, while keeping the DALL-E 2 variation path.
- Updated legacy OpenAI image helper paths and image-generation services to default to GPT Image 2 and support OpenAI reference images where model-compatible.
- Added and updated unit tests for model aliases, provider payloads, reference-image edits, normalization, UI metadata, and image size validation.

## Validation

- Verified official OpenAI documentation: the latest OpenAI image model ID is `gpt-image-2`; `img-gen-2` is treated as an alias in this repository.
  - https://platform.openai.com/docs/guides/image-generation
  - https://developers.openai.com/api/docs/models/gpt-image-2
- Passed Python syntax check with `python -m py_compile` over modified backend application files.
- Passed targeted tests:
  - `pytest tests/unit/test_model_utils.py tests/unit/services/providers/test_image_param_utils.py tests/unit/services/providers/test_oai_image_provider.py tests/unit/services/image/test_image_providers.py tests/unit/services/image/test_image_generation_service.py tests/unit/services/image_gen/test_normalize.py tests/unit/services/image_gen/test_ui_metadata_reference_images.py tests/unit/services/test_model_ui_image_gen_metadata.py -v --no-cov`
  - Result: `70 passed, 10 skipped, 77 warnings in 0.16s`.
- Re-ran targeted tests after pre-commit formatting changes:
  - `pytest tests/unit/test_model_utils.py tests/unit/services/providers/test_image_param_utils.py tests/unit/services/providers/test_oai_image_provider.py tests/unit/services/image/test_image_providers.py tests/unit/services/image/test_image_generation_service.py tests/unit/services/image_gen/test_normalize.py tests/unit/services/image_gen/test_ui_metadata_reference_images.py tests/unit/services/test_model_ui_image_gen_metadata.py -v --no-cov`
  - Result: `70 passed, 10 skipped, 77 warnings in 0.20s`.
- Attempted backend quick runner:
  - `python run_tests.py quick`
  - Result: failed before pytest during dependency installation because the resolver found a Python 3.13 conflict between the pinned `pydantic==2.5.0` and `langchain-core==0.2.43`, which requires `pydantic>=2.7.4` on Python `>=3.12.4`.
- Ran direct non-slow backend tests:
  - `pytest tests/ -m 'not slow' -v --no-cov`
  - Result: `2 failed, 1903 passed, 76 skipped, 20 deselected, 1354 warnings in 86.42s`.
  - The failures were in `tests/unit/services/audio/test_audio_generator.py::TestEnsureOSSConfigured::test_raises_when_none` and `tests/unit/services/audio/test_audio_generator.py::TestConcatMp3s::test_concat_mp3s`; those cover audio behavior outside this OpenAI image integration.
- Passed repository docs check:
  - `python scripts/check_repo_docs.py`
  - Result: `[check_repo_docs] ok`.
- Ran repository contract diff check on the GPT Image 2 changed files:
  - `python scripts/check_repo_contracts.py --mode diff <changed files>`
  - Result: failed on existing structural rules in changed legacy/oversized files, including oversized image/provider service modules, direct `.query(...)` hits in endpoint/diagnostic helpers, and the existing `ai_service_manager.py` legacy reference rule.
- Passed patch whitespace check:
  - `git diff --check`
- Ran pre-commit on this commit's file set:
  - `pre-commit run --files <changed files>`
  - Result: formatting/import hooks updated a few files, one unused test variable was fixed, and the backend pytest gate failed on the same two unrelated audio tests listed above.
  - Follow-up checks passed: `pre-commit run ruff --files <changed files>`, `pre-commit run black --files <changed files>`, and `pre-commit run isort --files <changed files>`.
- `pre-commit run --all-files` was not run because the worktree contains many unrelated user changes outside this commit scope. `./docker/build_prod_images.sh` was also not run; this is a backend provider wiring change and the existing audio/dependency validation failures need resolution before a full production gate is meaningful.
- Browser validation was not run. This change is backend provider/model wiring and request construction; no frontend route or browser flow was modified, and no live OpenAI API key smoke call was performed.

## Next Steps

- Resolve the existing audio unit-test failures if the full non-slow backend suite must be green before merge.
- Resolve the Python 3.13 dependency conflict in the backend quick runner environment if `python run_tests.py quick` is required.
- Optionally run a live OpenAI GPT Image 2 smoke test with a valid API key before enabling the model in production.

## Linked Commits

This commit: `feat(backend): add OpenAI GPT Image 2 support`
