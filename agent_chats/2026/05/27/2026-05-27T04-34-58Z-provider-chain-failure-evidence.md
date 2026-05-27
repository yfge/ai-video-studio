## User Prompt

继续处理 Timeline-first 内容质量验证里发现的问题。

## Goals

- Preserve real failure evidence for Seedance 400 responses emitted inside parallel video generation.
- Avoid Virtual IP name collisions across repeated live-quality runs and retries.

## Changes

- Updated provider-chain Virtual IP naming to use a SHA-1 suffix of the full run id instead of the last 12 characters.
- Added `VideoClipGenerationError` so parallel Seedance worker failures carry their request chain back to the parent payload.
- Added a regression test proving failed parallel video requests still write response evidence.

## Validation

- `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_media.py tests/scripts/test_provider_chain_api.py -q`
  - Result: `4 passed, 26 warnings`.
- `python scripts/check_repo_contracts.py --mode diff scripts/harness/provider_chain_api.py scripts/harness/provider_chain_media.py ai-pic-backend/tests/scripts/test_provider_chain_media.py`
  - Result: `[check_repo_contracts] ok (diff)`.
- `python scripts/check_repo_docs.py`
  - Result: `[check_repo_docs] ok`.
- `git diff --check`
  - Result: passed.

## Next Steps

- Re-run a small targeted provider-chain failure probe before spending another live-10 budget.
- Use the preserved 400 response bodies to decide whether to change Seedance prompt shape, duration/request parameters, or provider routing.

## Linked Commits

Pending
