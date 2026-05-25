---
id: 2026-05-25T18-27-39Z-provider-chain-timeline-first
date: 2026-05-25T18:27:39Z
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - harness
  - provider-chain
  - timeline
  - regression
related_paths:
  - scripts/harness/provider_chain_regression.py
  - scripts/harness/provider_chain_api.py
  - scripts/harness/provider_chain_media.py
  - scripts/harness/provider_chain_payloads.py
  - scripts/harness/provider_chain_timeline.py
  - ai-pic-backend/tests/scripts/test_provider_chain_regression.py
summary: Correct the provider-chain regression harness so Timeline seed is created before image/video generation, then update the same Timeline with generated assets before render.
---

## User Prompt

先生成时间轴！这一步你又造假了

## Goals

- Correct the provider-chain regression so Timeline remains the first-class source of truth.
- Ensure the harness creates a placeholder Timeline seed before Virtual IP image generation and before Seedance video generation.
- Generate video only from prompts and lineage stored in the existing Timeline seed.
- Update the same Timeline with generated video assets, then render from that updated Timeline.
- Keep request-chain evidence in `artifacts/runs/<run_id>/provider_chain.json`.

## Changes

- Reordered `provider_chain_regression.py` to run DeepSeek script generation, create Timeline seed, then create Virtual IP, OpenAI character image, Seedance videos, Timeline asset update, and Timeline render.
- Added `provider_chain_media.py` so Seedance generation reads `video_prompt`, duration, dialogue lineage, and clip ids from the Timeline seed instead of from the script directly.
- Reworked Timeline helpers:
  - `create_seed_timeline()` creates the placeholder Timeline with `timeline_first: true` and no video `asset_ref`.
  - `update_timeline_with_assets()` patches that same Timeline version with generated asset refs.
  - `render_timeline()` renders only after the asset update.
- Reworked payload helpers to build a Timeline seed spec and later attach generated video assets by `clip_id`.
- Removed the old direct `generate_videos(script, image)` helper from `provider_chain_api.py` to avoid a misleading non-Timeline-first generation path.
- Made Timeline asset attachment fail on `clip_id` mismatches instead of silently skipping missing or unused generated clips.
- Updated provider-chain tests to assert that the seed spec has placeholders/no assets first, generated assets preserve dialogue and provider lineage when attached, and clip id mismatches fail.

## Validation

- `python -m py_compile scripts/harness/provider_chain_regression.py scripts/harness/provider_chain_api.py scripts/harness/provider_chain_payloads.py scripts/harness/provider_chain_timeline.py scripts/harness/provider_chain_media.py` -> passed.
- `cd ai-pic-backend && PYTEST_ADDOPTS=--no-cov pytest tests/scripts/test_provider_chain_regression.py tests/unit/test_deepseek_provider_v4.py tests/unit/test_model_utils.py tests/unit/services/providers/test_oai_image_provider.py tests/unit/test_volcengine_provider_video.py -q` -> passed, 21 passed, 7 skipped, warnings only.
- Smoke system API run:
  - Command: `python scripts/harness/provider_chain_regression.py --mode smoke --run-id provider-chain-timeline-first-smoke-20260525T181057Z --api-url http://localhost:8000 --episode-id 133 --script-id 117 --timeout-seconds 1200 --poll-interval-seconds 5`
  - Artifact: `artifacts/runs/provider-chain-timeline-first-smoke-20260525T181057Z/provider_chain.json`
  - Result: `ok=True`
  - Timeline seed id/version: `14` / `1`; duration `4000`; clip count `1`.
  - Updated Timeline version: `2`.
  - Seedance task: `cgt-20260526021208-7rscw`.
  - Render job: `19`; final output `https://resource.lets-gpt.com/timeline-renders/video/20260525/181407/b47e0f93.mp4`.
  - Request order confirmed: `timeline-create` before `openai-character-image`, before `seedance-video-1`, before `timeline-assets-update`, before `timeline-render-queue`.
- Full 30s system API run:
  - Command: `python scripts/harness/provider_chain_regression.py --mode full-30s --run-id provider-chain-timeline-first-full-30s-20260525T181523Z --api-url http://localhost:8000 --episode-id 133 --script-id 117 --timeout-seconds 1800 --poll-interval-seconds 5`
  - Artifact: `artifacts/runs/provider-chain-timeline-first-full-30s-20260525T181523Z/provider_chain.json`
  - Result: `ok=True`
  - Timeline seed id/version: `15` / `1`; duration `30000`; clip count `2`.
  - Updated Timeline version: `2`.
  - Seedance tasks: `cgt-20260526021633-dk8qw`, `cgt-20260526022340-wrbpc`.
  - Render job: `20`; final output `https://resource.lets-gpt.com/timeline-renders/video/20260525/182712/8db3b5f0.mp4`.
  - Request order confirmed: `timeline-create` before `openai-character-image`, before `seedance-video-1`, before `timeline-assets-update`, before `timeline-render-queue`.
  - Production quality checks passed: character image URL present, every clip has dialogue source, video prompt, and task/video lineage.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/tests/scripts/test_provider_chain_regression.py scripts/harness/provider_chain_api.py scripts/harness/provider_chain_payloads.py scripts/harness/provider_chain_regression.py scripts/harness/provider_chain_timeline.py scripts/harness/provider_chain_media.py agent_chats/2026/05/25/2026-05-25T18-27-39Z-provider-chain-timeline-first.md` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files ai-pic-backend/tests/scripts/test_provider_chain_regression.py scripts/harness/provider_chain_api.py scripts/harness/provider_chain_payloads.py scripts/harness/provider_chain_regression.py scripts/harness/provider_chain_timeline.py scripts/harness/provider_chain_media.py agent_chats/2026/05/25/2026-05-25T18-27-39Z-provider-chain-timeline-first.md` -> first run reformatted one test file with black; second run passed all hooks, including backend quick gate. Frontend lint skipped because no frontend files changed.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> passed. Backend and frontend images built locally with tag `23a5fb19`; no registry push.

## Next Steps

- Consider adding incremental harness logging so long external provider runs show the current stage instead of only printing at completion.

## Linked Commits

Pending
