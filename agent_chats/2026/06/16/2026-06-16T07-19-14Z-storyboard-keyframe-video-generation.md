---
id: storyboard-keyframe-video-generation
date: 2026-06-16T07:19:14Z
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - ai-video-studio
  - timeline
  - storyboard
  - keyframes
  - video-generation
related_paths:
  - ai-pic-backend/app/services/timeline_clip_visual_prompt_builder.py
  - ai-pic-backend/app/services/timeline_clip_keyframe_service.py
  - ai-pic-backend/app/services/timeline_clip_video_rework_queue_service.py
  - ai-pic-backend/tests/test_timeline_clip_video_rework_lineage_api.py
  - ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControls.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkCards.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipSharedReferenceContext.tsx
  - ai-pic-frontend/tests/timelineClipReworkControls.test.ts
summary: Clip storyboard, start/end keyframe, and video generation interaction and prompt contract improvements.
---

## User Prompt

优化故事板，视频首尾帧，以及视频生成的交互，和相应的提示词生成逻辑 必要时上网查询相关内容

## Goals

- Clarify the selected-clip storyboard, start/end keyframe, and video generation workflow.
- Share backend prompt construction for keyframe prompts and default start/end video motion prompts.
- Keep existing public API request payloads compatible while adding prompt provenance metadata to queued task payloads.
- Make selected reference context, keyframe readiness, and unavailable reference sources visible in the Timeline production controls.

## Changes

- Added `timeline_clip_visual_prompt_builder.py` with `timeline_clip_visual_prompt_v1`, motion-timeline extraction, distinct start/end keyframe prompts, video motion prompt rendering, and prompt source metadata.
- Updated keyframe queueing to use the shared builder and include `prompt_contract_version`, `visual_prompt_source`, and `motion_prompt_source`.
- Updated default start/end video rework queueing to use the shared motion prompt while leaving clip storyboard panel and grid panel prompt paths unchanged.
- Added a shared reference context above selected-clip production actions, moved manual reference URLs there, and kept IP/environment thumbnail controls visible.
- Added keyframe readiness copy and disabled the start/end video reference source when the selected clip has no generated start frame.
- Renamed the video prompt field to motion override and added empty-state copy for Timeline motion planning.
- Added design and active implementation plan docs.

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest tests/unit/services/test_timeline_clip_visual_prompt_builder.py tests/test_timeline_clip_keyframe_api.py tests/test_timeline_clip_video_rework_api.py tests/test_timeline_clip_video_rework_lineage_api.py tests/test_timeline_clip_video_grid_rework_api.py -v` -> pass, 13 passed.
- `cd ai-pic-backend && python run_tests.py quick` -> did not reach pytest; dependency install failed under Python 3.13 because `langchain-core==0.2.43` requires `pydantic>=2.7.4` while repo requirements pin `pydantic==2.5.0`.
- `cd ai-pic-frontend && npx tsx --test tests/timelineClipReworkControls.test.ts` -> pass, 18 passed.
- `cd ai-pic-frontend && npm run lint` -> pass with 3 warnings in unrelated baseline files: `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && npm run test` -> interrupted after stalling with no new output; the updated `timeline clip rework controls` suite had passed before the stall, but this full frontend script is not counted as passing.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> pass.
- `python scripts/check_repo_contracts.py --mode audit` -> pass.
- `git diff --check -- docs ai-pic-backend ai-pic-frontend agent_chats` -> pass.
- `pre-commit run --all-files` -> failed on existing all-files baseline issues: `ruff` reported unrelated existing violations, `backend-pytest` hit 11 collection import errors around `production_quality_script` and `scripts_ai_manager` symbols, and all-files format hooks modified unrelated historical files. Hook-generated unrelated file edits were restored and not included in this delivery commit.
- `./docker/build_prod_images.sh` -> pass; backend and frontend multi-arch production images built and pushed with `IMAGE_TAG=5f3bb528`. Frontend image `npm ci --omit=dev` reported existing npm audit output with 2 vulnerabilities, but the script completed successfully.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089`.
- Harness run id: `storyboard-keyframe-video-generation-20260616T071528Z`.
- `python scripts/harness/doctor.py --run-id storyboard-keyframe-video-generation-20260616T071528Z` -> failed because standalone frontend port `3000` was closed; Nginx `8089` and backend `/health` were available.
- `HARNESS_USER=... HARNESS_PASSWORD=... python scripts/harness/browser_flow.py --scenario episode_timeline_smoke --run-id storyboard-keyframe-video-generation-20260616T071528Z` -> pass with `engine=playwright`, `selected_status=degraded`; Chrome DevTools at `127.0.0.1:9222` was unavailable.
- Stock browser scenario opened `http://localhost:8089/episodes/124/workspace?tab=timeline&scriptId=127`, confirmed the Timeline workspace loaded, and recorded API 200 responses for episode, scripts, timelines, characters, environments, and model availability. Scenario gap: episode 124 had no video track, so it did not render selected-clip production controls.
- Additional Playwright selected-clip check opened `http://localhost:8089/episodes/6/workspace?tab=timeline&clipId=video_scene_001_beat_001_001&scriptId=8`; artifact: `artifacts/runs/storyboard-keyframe-video-generation-20260616T071528Z/selected_clip_production_controls.json`.
- Selected-clip evidence found `片段共享参考上下文`, `视频参考来源`, `生成首尾帧`, `片段分镜图`, `片段视频`, and `首尾帧待生成`; confirmed shared context is outside collapsed parameter details; confirmed `textarea[aria-label="运动提示词覆盖"]` exists.
- Selected-clip video reference options were: `首尾帧（需先生成）` disabled, `分镜 Panel 1` enabled, `手动/共享参考图` enabled.
- Console evidence contained only React DevTools/HMR logs plus one resource error from fixture URL `https://cdn.example/browser-courier-20260609.png`; local app/API requests for the selected clip returned 200.

3. Conflict signals and corrections:

- Initial browser assumption: the stock `episode_timeline_smoke` scenario would cover selected-clip production controls.
- Contradicting evidence: DOM snapshot for episode 124 did not contain the new labels and the page showed `无视频轨`.
- Reproduction and fix: queried existing local episodes read-only, found episode 6 with timeline 66 and video clip `video_scene_001_beat_001_001`, then reran a selected-clip Playwright inspection.
- Final verified state: selected-clip controls rendered the new shared reference context, keyframe readiness, disabled start/end reference source, and motion override field in the local app.

## Next Steps

- Run a provider-backed generation task when real provider credentials and a safe sample clip are available, because this change intentionally stops at queue payloads and UI readiness rather than calling external video/image providers.
- Resolve the repo-level backend dependency conflict before relying on `python run_tests.py quick` under Python 3.13.
- Investigate the full frontend `npm run test` hang separately; the focused changed suite passed.

## Linked Commits

- Pending
