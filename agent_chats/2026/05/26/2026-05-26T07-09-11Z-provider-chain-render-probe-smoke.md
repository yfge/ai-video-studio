---
id: 2026-05-26T07-09-11Z-provider-chain-render-probe-smoke
date: "2026-05-26T07:09:11Z"
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
related_paths:
  - tasks.md
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - docs/exec-plans/active/timeline-main-chain.md
summary: Record live provider-chain smoke evidence for the automated render media probe.
---

## User Prompt

提交，然后继续推进。

## Goals

- After committing the harness probe implementation, run a real provider-chain smoke regression to prove the new `render_media_probe` is written by the harness automatically.
- Keep the evidence scoped to chain correctness and final media structure; do not overstate it as content-quality proof.

## Changes

- Updated `tasks.md` with the live smoke evidence.
- Updated active execution plans with Timeline id, render job id, final URL, duration probe, and extracted frame evidence.

## Validation

- `python scripts/harness/provider_chain_regression.py --mode smoke --run-id provider-chain-render-probe-smoke-20260526T071200Z --api-url http://localhost:8000 --episode-id 133 --script-id 117 --timeout-seconds 1200 --poll-interval-seconds 5` passed.
- Evidence: `artifacts/runs/provider-chain-render-probe-smoke-20260526T071200Z/provider_chain.json`.
- Timeline `20` was created before media generation with `dialogue=1`, `video=1`, and `subtitle=1`.
- DeepSeek `deepseek-v4-flash` generated script title `Glimmer in the Garden`.
- MiniMax `speech-2.6-hd` generated one dialogue audio URL.
- OpenAI `gpt-image-2` generated and persisted character image `https://resource.lets-gpt.com/ai-generated/virtual-ip/image/20260526/070256/a5cffec1.png`.
- Volcengine `doubao-seedance-2-0-260128` generated one 4 second clip with task id `cgt-20260526150257-kzrbb`.
- Render job `28` succeeded with output `https://resource.lets-gpt.com/timeline-renders/video/20260526/070808/ada257bc.mp4`.
- `render_media_probe.ok=true`; expected duration `4.0s`, final video duration `4.041667s`, final audio duration `4.032s`, and all probe checks passed.
- Extracted frame `artifacts/runs/provider-chain-render-probe-smoke-20260526T071200Z/frames/render_scene_01_2000ms.jpg` was visually inspected; it shows the 3D cartoon robot and readable subtitle `Botty: Oh! A light?`.
- Browser/Chrome validation was not claimed; this was a system API harness regression plus ffprobe and extracted-frame evidence.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` passed; no changed-file diff rules applied.
- `git diff --check` passed.
- `pre-commit run --files <changed files>` passed, including repository docs, contracts, and ledger enforcement. Backend quick gate and frontend lint were skipped because no backend/frontend runtime files changed.

## Next Steps

- The remaining risk is production quality, not chain structure: character consistency over multiple clips, lip-sync, acting direction, and content taste still need scored sample runs.

## Linked Commits

Pending
