---
id: 2026-05-26T03-45-24Z-provider-chain-dialogue-tracks
date: 2026-05-26T03:45:24Z
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - harness
  - provider-chain
  - timeline
  - dialogue
  - subtitles
related_paths:
  - scripts/harness/provider_chain_regression.py
  - scripts/harness/provider_chain_payloads.py
  - scripts/harness/provider_chain_timeline_payloads.py
  - scripts/harness/provider_chain_timeline.py
  - ai-pic-backend/tests/scripts/test_provider_chain_regression.py
  - tasks.md
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - docs/exec-plans/active/timeline-main-chain.md
  - docs/exec-plans/active/timeline-main-chain-optimization.md
summary: Extend the provider-chain Timeline seed so script dialogue and subtitles are first-class Timeline tracks before media generation.
---

## User Prompt

继续

## Goals

- Continue tightening the provider-chain regression after the Timeline-first fix.
- Stop treating dialogue as hidden prompt metadata only.
- Create a Timeline seed with explicit `dialogue`, `video`, and `subtitle` tracks before image/video generation.
- Keep video generation driven by the seed Timeline's video clips.
- Record the remaining truth clearly: current render consumes video clips only, so this is not proof of burned-in subtitles or TTS dialogue.

## Changes

- Added `scripts/harness/provider_chain_timeline_payloads.py` to own provider-chain Timeline seed, asset-attachment, track-count, and quality-check logic.
- Kept `provider_chain_payloads.py` focused on provider constants, script parsing, and prompt construction so it stays well below the file-size hard limit.
- Changed the provider-chain seed Timeline to include one dialogue clip and one subtitle clip per DeepSeek scene, aligned to the same timing as the video clip.
- Strengthened quality checks to require dialogue/video/subtitle track counts, subtitle text, dialogue text, provider task lineage, video prompt lineage, and character image URL.
- Updated tests to assert the seed contains `dialogue`, `video`, and `subtitle` tracks before generated video assets are attached.
- Updated `tasks.md` and active execution plans with the new provider-backed Timeline-first evidence and the render limitation.

## Validation

- `python -m py_compile scripts/harness/provider_chain_regression.py scripts/harness/provider_chain_api.py scripts/harness/provider_chain_payloads.py scripts/harness/provider_chain_timeline.py scripts/harness/provider_chain_media.py scripts/harness/provider_chain_timeline_payloads.py` -> passed.
- `cd ai-pic-backend && PYTEST_ADDOPTS=--no-cov pytest tests/scripts/test_provider_chain_regression.py -q` -> passed, 4 tests, warnings only.
- `cd ai-pic-backend && PYTEST_ADDOPTS=--no-cov pytest tests/scripts/test_provider_chain_regression.py tests/unit/test_deepseek_provider_v4.py tests/unit/test_model_utils.py tests/unit/services/providers/test_oai_image_provider.py tests/unit/test_volcengine_provider_video.py -q` -> passed, 21 passed, 7 skipped, warnings only.
- System API smoke:
  - Command: `python scripts/harness/provider_chain_regression.py --mode smoke --run-id provider-chain-dialogue-tracks-smoke-20260526T033733Z --api-url http://localhost:8000 --episode-id 133 --script-id 117 --timeout-seconds 1200 --poll-interval-seconds 5`
  - Artifact: `artifacts/runs/provider-chain-dialogue-tracks-smoke-20260526T033733Z/provider_chain.json`
  - Result: `ok=True`.
  - Timeline seed: id `16`, version `1`, duration `4000`, track counts `dialogue=1`, `video=1`, `subtitle=1`.
  - Request order: `timeline-create` before `openai-character-image`, before `seedance-video-1`, before `timeline-assets-update`, before `timeline-render-queue`.
  - Seedance task: `cgt-20260526113818-n6tl8`.
  - Render job: `21`, succeeded with output `https://resource.lets-gpt.com/timeline-renders/video/20260526/034336/739ae690.mp4`.
  - Production quality checks passed, including dialogue/subtitle track checks.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/tests/scripts/test_provider_chain_regression.py docs/exec-plans/active/main-chain-commercial-readiness.md docs/exec-plans/active/timeline-main-chain-optimization.md docs/exec-plans/active/timeline-main-chain.md scripts/harness/provider_chain_payloads.py scripts/harness/provider_chain_regression.py scripts/harness/provider_chain_timeline.py scripts/harness/provider_chain_timeline_payloads.py tasks.md agent_chats/2026/05/26/2026-05-26T03-45-24Z-provider-chain-dialogue-tracks.md` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files ai-pic-backend/tests/scripts/test_provider_chain_regression.py docs/exec-plans/active/main-chain-commercial-readiness.md docs/exec-plans/active/timeline-main-chain-optimization.md docs/exec-plans/active/timeline-main-chain.md scripts/harness/provider_chain_payloads.py scripts/harness/provider_chain_regression.py scripts/harness/provider_chain_timeline.py scripts/harness/provider_chain_timeline_payloads.py tasks.md agent_chats/2026/05/26/2026-05-26T03-45-24Z-provider-chain-dialogue-tracks.md` -> passed. Backend quick gate passed; frontend lint skipped because no frontend files changed.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> passed. Backend and frontend images built locally with tag `f782142b`; no registry push.

## Next Steps

- Next honest quality boundary: render worker currently consumes video track only. Burned-in subtitles or TTS dialogue requires a separate render/audio implementation and validation run.

## Linked Commits

Pending
