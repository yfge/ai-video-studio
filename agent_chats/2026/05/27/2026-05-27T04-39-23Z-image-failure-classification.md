## User Prompt

继续处理真实 provider 回归中发现的问题。

## Goals

- Classify OpenAI image generation endpoint failures accurately in provider-chain artifacts.
- Keep the quality report from hiding image failures under `unknown`.

## Changes

- Updated provider-chain failure categorization for `/virtual-ips/{id}/images/generate` and `AI图像生成失败`.
- Added a targeted regression test for image generation endpoint failure classification.

## Validation

- `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_regression.py tests/scripts/test_provider_chain_media.py -q`
  - Result: `9 passed, 26 warnings`.
- `python scripts/check_repo_contracts.py --mode diff scripts/harness/provider_chain_regression.py ai-pic-backend/tests/scripts/test_provider_chain_regression.py`
  - Result: `[check_repo_contracts] ok (diff)`.
- `python scripts/check_repo_docs.py`
  - Result: `[check_repo_docs] ok`.
- `git diff --check`
  - Result: passed.
- Targeted probe:
  - `seedance-400-probe-20260527T043528Z` stopped at `openai-character-image` with 500.
  - Response body: `{"detail":"AI图像生成失败"}`.

## Next Steps

- Do not spend another live-10 run until image generation and Seedance 400 request bodies are diagnosed.
- The current quality verdict remains `not_trial_ready`.

## Linked Commits

Pending
