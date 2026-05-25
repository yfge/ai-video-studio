---
id: 2026-05-25T17-32-02Z-provider-chain-regression
date: 2026-05-25T17:32:02Z
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - harness
  - provider-chain
  - ai-generation
  - timeline
related_paths:
  - ai-pic-backend/app/services/providers/volcengine_provider/video.py
  - ai-pic-backend/tests/unit/test_volcengine_provider_video.py
  - scripts/harness/provider_chain_regression.py
  - scripts/harness/provider_chain_api.py
  - scripts/harness/provider_chain_payloads.py
  - scripts/harness/provider_chain_timeline.py
  - ai-pic-backend/tests/scripts/test_provider_chain_regression.py
summary: Add a system API provider-chain regression harness for DeepSeek script, OpenAI image, Seedance video, and optional Timeline render evidence.
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN: 新增真实系统 API 回归计划，按系统 API 串起 DeepSeek 生成剧本/对白、OpenAI GPT Image 2 生成并持久化卡通角色图、Seedance 2.0 生成视频；记录 provider、model、task_id、图片 URL、视频 URL；支持 smoke 和 full-30s，并保留 evidence JSON。

## Goals

- Add a rerunnable provider-chain harness under `scripts/harness/`.
- Keep the chain honest: no manual stitched video and no generated media without source lineage.
- Use 2D/3D cartoon character prompts to avoid live-action human restrictions.
- Persist request/response evidence under `artifacts/runs/<run_id>/provider_chain.json`.
- Keep the harness and helpers within repository file-size limits.

## Changes

- Added `provider_chain_regression.py` as the CLI entrypoint.
- Added API helpers for login, model availability checks, DeepSeek text generation, Virtual IP creation, OpenAI character image generation, and Seedance video generation.
- Added payload helpers for structured script extraction, prompt construction, smoke/full duration policy, Timeline Spec construction, and lineage quality checks.
- Added Timeline/render helper functions for full-30s composition and render polling.
- Added offline tests for script JSON parsing, mode duration splitting, and Timeline lineage preservation.
- Fixed the synchronous Volcengine i2v success path so prompt metadata is read
  from the text content item instead of assuming `content[0]` is text.
- Added a Volcengine regression test for Seedance i2v prompt extraction and
  added harness error-body capture for failed HTTP responses.

## Validation

1. Local checks:

- `python -m py_compile scripts/harness/provider_chain_regression.py scripts/harness/provider_chain_api.py scripts/harness/provider_chain_payloads.py scripts/harness/provider_chain_timeline.py` -> passed.
- `wc -l scripts/harness/provider_chain_api.py scripts/harness/provider_chain_payloads.py scripts/harness/provider_chain_timeline.py scripts/harness/provider_chain_regression.py ai-pic-backend/tests/scripts/test_provider_chain_regression.py` -> all files under the 300-line hard limit.
- `cd ai-pic-backend && PYTEST_ADDOPTS=--no-cov pytest tests/scripts/test_provider_chain_regression.py -q` -> passed, 3 tests, warnings only.
- `cd ai-pic-backend && PYTEST_ADDOPTS=--no-cov pytest tests/scripts/test_provider_chain_regression.py tests/unit/test_deepseek_provider_v4.py tests/unit/test_model_utils.py tests/unit/services/providers/test_oai_image_provider.py tests/unit/test_volcengine_provider_video.py -q` -> passed, 20 tests, 7 skipped, warnings only.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> passed.
- `git diff --check` -> passed before pre-commit formatting.
- `pre-commit run --files <changed files>` -> first run passed ruff/black/docs/contracts/ledger/backend quick gate but isort reformatted two test files; second run passed all configured hooks, backend quick gate passed, frontend lint skipped because no frontend files changed.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> passed. Backend and frontend images built locally with tag `295798bf`; no registry push. The frontend image build emitted the existing npm audit summary `2 vulnerabilities (1 moderate, 1 high)`.

2. Browser or MCP validation:

- Chrome MCP validation was attempted but the DevTools transport was not
  available: `Could not connect to Chrome ... http://127.0.0.1:9222/json/version:
HTTP Not Found`.
- Fallback media validation:
  `curl -L -I https://resource.lets-gpt.com/timeline-renders/video/20260525/175313/f4c674ca.mp4`
  -> HTTP 200, `Content-Type: video/mp4`, `Content-Length: 12137549`,
  `x-oss-meta-clip-count: 2`, `x-oss-meta-duration-ms: 30000`,
  `x-oss-meta-render-job-id: 18`, `x-oss-meta-timeline-id: 13`.
- `ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 https://resource.lets-gpt.com/timeline-renders/video/20260525/175313/f4c674ca.mp4`
  -> `duration=30.161224`, `size=12137549`.

3. System API provider-chain validation:

- `python scripts/harness/provider_chain_regression.py --mode smoke --run-id provider-chain-smoke-20260525T173251Z --api-url http://localhost:8000 --timeout-seconds 1200` -> failed at Seedance with backend/provider error `volcengine 错误: 'text'`; DeepSeek script and OpenAI image persistence had already succeeded.
- `python scripts/harness/provider_chain_regression.py --mode smoke --run-id provider-chain-smoke-20260525T173813Z --api-url http://localhost:8000 --timeout-seconds 1200` -> passed. Evidence: `artifacts/runs/provider-chain-smoke-20260525T173813Z/provider_chain.json`; image provider/model `openai/gpt-image-2`; video provider/model `volcengine/doubao-seedance-2-0-260128`; task id `cgt-20260526013929-9j5pc`.
- `python scripts/harness/provider_chain_regression.py --mode full-30s --run-id provider-chain-full-30s-20260525T174203Z --api-url http://localhost:8000 --episode-id 133 --script-id 117 --timeout-seconds 2400 --poll-interval-seconds 5` -> passed. Evidence: `artifacts/runs/provider-chain-full-30s-20260525T174203Z/provider_chain.json`.
- Full run output: DeepSeek script provider/model `deepseek/deepseek-v4-flash`; OpenAI image URL `https://resource.lets-gpt.com/ai-generated/virtual-ip/image/20260525/174305/24c48ec4.png`; Seedance tasks `cgt-20260526014307-h2clg` and `cgt-20260526014850-gvtgk`; Timeline id `13`; render job id `18`; final output `https://resource.lets-gpt.com/timeline-renders/video/20260525/175313/f4c674ca.mp4`.
- Harness quality checks passed: character image URL present, all clips have dialogue source, all clips have video prompt, and all clips have lineage.

4. Conflict signals and corrections:

- The target `/api/v1/virtual-ips/{id}/images/generate` route exists through the `virtual_ip_images` router, not the core `virtual_ip` CRUD router.
- The harness is split into entrypoint, API, payload, and Timeline helpers to stay inside Python file-size limits.
- The first real smoke exposed a production bug: synchronous Seedance i2v returned success from Volcengine, but backend metadata extraction crashed because the first content item is `first_frame`, not text. The fix now scans content for the text item.
- The full-30s script generated two characters but the harness intentionally creates a single主角 anchor image. That is enough for this provider-chain regression, not proof of full multi-character consistency.

## Next Steps

- Rerun pre-commit after isort formatting.
- Commit as one atomic provider-chain harness and Seedance i2v fix.

## Linked Commits

Pending
