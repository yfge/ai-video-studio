---
id: 2026-05-26T07-29-03Z-provider-chain-full-render-probe
date: "2026-05-26T07:29:03Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - provider-chain
  - timeline
  - render
  - evidence
  - latency
related_paths:
  - scripts/harness/provider_chain_api.py
  - ai-pic-backend/tests/scripts/test_provider_chain_api.py
  - tasks.md
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - docs/exec-plans/active/timeline-main-chain.md
summary: Record the full-30s render-probe regression and add request duration evidence to provider-chain harness entries.
---

## User Prompt

提交，然后继续推进。

## Goals

- Run the updated provider-chain harness in `full-30s` mode so the final render probe is produced automatically on a 30 second chain.
- Add request-chain duration recording so future evidence JSON captures provider latency without requiring Docker log archaeology.
- Keep the conclusion honest: this proves chain structure and media duration, not commercial content quality.

## Changes

- Added `duration_seconds` to `request_chain` entries recorded by `scripts/harness/provider_chain_api.py`.
- Added a focused unit test for duration capture in `ai-pic-backend/tests/scripts/test_provider_chain_api.py`.
- Updated `tasks.md` and active execution plans with the full-30s render-probe evidence and observed Seedance latency.

## Validation

- `python scripts/harness/provider_chain_regression.py --mode full-30s --run-id provider-chain-render-probe-full-30s-20260526T071051Z --api-url http://localhost:8000 --episode-id 133 --script-id 117 --timeout-seconds 1800 --poll-interval-seconds 5` passed.
- Evidence: `artifacts/runs/provider-chain-render-probe-full-30s-20260526T071051Z/provider_chain.json`.
- Timeline `21` was created before media generation with `dialogue=2`, `video=2`, and `subtitle=2`.
- DeepSeek `deepseek-v4-flash` generated title `机器人的发现`.
- MiniMax `speech-2.6-hd` generated two dialogue audio URLs.
- OpenAI `gpt-image-2` generated and persisted character image `https://resource.lets-gpt.com/ai-generated/virtual-ip/image/20260526/071200/f16f1426.png`.
- Volcengine `doubao-seedance-2-0-260128` generated two 15 second clips with task ids `cgt-20260526151201-zldt7` and `cgt-20260526151844-8xd9h`.
- Render job `29` succeeded with output `https://resource.lets-gpt.com/timeline-renders/video/20260526/072611/d4b917fa.mp4`.
- `render_media_probe.ok=true`; expected duration `30.0s`, final video duration `30.125s`, final audio duration `30.08s`, and all probe checks passed.
- Extracted frames `frames/render_scene_01_2000ms.jpg` and `frames/render_scene_02_17000ms.jpg` were visually inspected. Both show a 3D cartoon robot and readable Chinese subtitles, but this is still not proof of production-grade character consistency or acting quality.
- Backend logs show the two 15 second Seedance calls took about `402.957s` and `440.514s`; this is a real operational latency risk for full-30s live regression.
- `python -m py_compile scripts/harness/provider_chain_api.py` passed.
- `cd ai-pic-backend && PYTEST_ADDOPTS=--no-cov pytest tests/scripts/test_provider_chain_api.py tests/scripts/test_provider_chain_regression.py tests/scripts/test_provider_chain_render_probe.py -q` passed: `8 passed, 26 warnings`.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` passed.
- `git diff --check` passed.
- `pre-commit run --files <changed files>` passed, including repository docs, contracts, ledger enforcement, and backend quick gate.

## Next Steps

- Treat 4 second smoke as the normal live regression gate and keep full-30s as a low-frequency paid gate unless provider video generation becomes asynchronous and observable.
- Production-quality work still needs scored multi-sample review: character consistency, lip-sync, acting direction, and story quality.

## Linked Commits

Pending
