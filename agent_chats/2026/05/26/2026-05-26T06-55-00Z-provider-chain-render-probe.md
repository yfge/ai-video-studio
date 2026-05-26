---
id: 2026-05-26T06-55-00Z-provider-chain-render-probe
date: "2026-05-26T06:55:00Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - provider-chain
  - timeline
  - render
  - harness
  - ffprobe
related_paths:
  - scripts/harness/provider_chain_regression.py
  - scripts/harness/provider_chain_render_probe.py
  - ai-pic-backend/tests/scripts/test_provider_chain_regression.py
  - ai-pic-backend/tests/scripts/test_provider_chain_render_probe.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - docs/exec-plans/active/timeline-main-chain.md
  - docs/exec-plans/active/timeline-main-chain-optimization.md
  - tasks.md
summary: Add final render media probing to the provider-chain regression harness.
---

## User Prompt

提交，然后继续推进。此前用户强调“时间第一性”，要求真实系统 API 回归不能绕过 Timeline，也不能把手工拼片或单段视频冒充全流程。

## Goals

- 让 provider-chain harness 在完成 `render_timeline` 后继续验证最终成片，而不是只信任 API 返回成功。
- 把最终 render 的音视频流、Timeline duration 和场景抽帧记录到可复跑 evidence。
- 保持真实结论边界：这证明链路和最终媒体结构，不证明商业级角色一致性、表演、口型或内容质量。

## Changes

- Added `scripts/harness/provider_chain_render_probe.py`.
- Wired `provider_chain_regression.py` so successful Timeline render now runs a media probe before declaring the harness passed.
- The probe writes `render_ffprobe.json`, checks final output URL, video stream, audio stream, expected Timeline duration, and extracts one frame per Timeline scene into `artifacts/runs/<run_id>/frames/`.
- Added regression tests for successful stream/frame recording and failure when the final render lacks an audio stream, split into a separate file to stay within repository file-size limits.
- Updated `tasks.md` and active execution plans to record that later provider-chain runs automatically capture final render media evidence.

## Validation

- `python -m py_compile scripts/harness/provider_chain_regression.py scripts/harness/provider_chain_render_probe.py` passed.
- `cd ai-pic-backend && PYTEST_ADDOPTS=--no-cov pytest tests/scripts/test_provider_chain_regression.py tests/scripts/test_provider_chain_render_probe.py -q` passed: `7 passed, 26 warnings`.
- Manual probe against the prior real full-30s output passed and wrote `artifacts/runs/provider-chain-dialogue-segments-full-30s-20260526T045229Z/render_media_probe_manual.json`.
- Manual probe result: output `https://resource.lets-gpt.com/timeline-renders/video/20260526/051434/7849fd70.mp4`, video `30.125s`, audio `30.080s`, scene frames `frames/render_scene_01_2000ms.jpg` and `frames/render_scene_02_17000ms.jpg`.
- Visually inspected `frames/render_scene_02_17000ms.jpg`; it shows the robot close-up and readable Chinese subtitles.
- Browser/Chrome validation was not claimed. This change is a CLI harness evidence gate, and the visual evidence is the extracted render frames.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` passed.
- `git diff --check` passed.
- `pre-commit run --files <changed files>` passed, including repository docs, contracts, ledger enforcement, and backend quick gate.
- `./docker/build_prod_images.sh` was not rerun for this harness-only change; the previous commit in this session reran the production Docker build after Dockerfile changes.

## Next Steps

- Run the updated provider-chain harness on the next paid/live regression so `provider_chain.json` includes the new `render_media_probe` artifact automatically.
- Keep production-quality judgment separate from this pass/fail gate: character consistency, lip-sync, acting quality, and repeatable sample quality still need scored sample runs.

## Linked Commits

Pending
