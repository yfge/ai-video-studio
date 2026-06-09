## User Prompt

`/goal 视频部分没有看到绑定 IP 环境`

Active goal context also covered the episode workspace URL
`http://localhost:8089/episodes/340cacb9ed854bb18d50f2c69547bf03/workspace?tab=storyboard&scriptId=142`
and required the storyboard, first/last-frame image, IP/environment binding, and video generation flow to be made coherent.

## Goals

- Make the storyboard tab expose a real clip-scoped storyboard management entry for native Timeline video clips.
- Preserve the boundary that the storyboard tab does not reintroduce whole-Timeline storyboard grid generation.
- Let the management entry deep-link into the Timeline tab with the selected `clipId`.
- Make the Timeline tab's lower production panel clearly name the selected clip management area.

## Changes

- Added `WorkspaceStoryboardClipManagement` and supporting model/status helpers to list native video clips on the storyboard tab.
- Each video clip row now summarizes environment/IP binding, clip storyboard reference, first/last-frame readiness, and final video readiness from the available Timeline/storyboard state.
- The `进入分镜管理` link now routes to `tab=timeline&scriptId=<id>&clipId=<clip_id>`.
- The episode workspace page passes `clipId` from the URL through the active tab content into the Timeline workspace.
- The Timeline workspace now honors an initial clip deep link once, then still allows normal user selection.
- The selected video clip production section is now labeled `片段分镜管理`.
- The video generation card now shows a dedicated `视频生成绑定上下文` summary so the IP/environment binding state is visible inside the video section, not only in the storyboard reference controls.
- Added a clip-scoped `首尾帧` generation step between storyboard reference and final video generation.
- Added `POST /api/v1/timelines/{timeline_id}/clips/{clip_id}/keyframes/generate` to queue Timeline-native start/end keyframe image generation.
- Added a keyframe processor that persists generated images, writes `start_frame_asset_ref` and `end_frame_asset_ref` back to the selected Timeline video clip, and syncs clip asset lineage.
- Added frontend tests for storyboard tab clip management and Timeline clip deep-link selection.
- Added frontend coverage that selected IP/environment reference images remain visible in the video card and are still submitted with the video rework payload.
- Added backend and frontend coverage for keyframe task queueing, keyframe processor writeback, API client routing, and IP/environment binding propagation into the keyframe request.
- Changed the Timeline clip environment panel so a video clip without a matched normalized scene can still select an environment for clip generation context.
- Kept scene environment persistence scoped to matched normalized scenes; unmatched clips show the environment as `片段生成参考` and do not call the scene update API.
- Added an empty角色 IP state in the storyboard/video binding card with a direct `去临时角色绑定 IP` action.
- Threaded the `临时角色` navigation action from the Timeline workspace into the clip video binding controls.

## Validation

- `cd ai-pic-frontend && npm run test` passed: 50 tests.
- After adding keyframes, `cd ai-pic-frontend && npm run test` passed: 52 tests.
- `cd ai-pic-frontend && npx tsx --test tests/timelineClipReworkControls.test.ts` passed: 12 tests.
- `cd ai-pic-frontend && npx tsx --test tests/timelineApiEndpoints.test.ts tests/timelineClipReworkControls.test.ts` passed: 15 tests.
- `cd ai-pic-frontend && npm run lint` passed with 3 existing warnings:
  - `eslint.config.mjs` anonymous default export warning.
  - Existing `<img>` warnings in `EnvironmentReferenceImagesField.tsx` and `VirtualIPReferenceImagesField.tsx`.
- `python scripts/check_repo_contracts.py --mode diff ...` passed for the changed frontend files.
- `python scripts/check_repo_contracts.py --mode diff ...` passed for the expanded backend/frontend changed-file set.
- `python scripts/check_repo_contracts.py --mode audit` passed.
- `python scripts/check_repo_docs.py` passed.
- `cd ai-pic-frontend && npm run build` passed.
- `cd ai-pic-frontend && npm run test -- timelineWorkspaceLayout.test.tsx` passed through the full frontend test runner: 53 tests.
- `cd ai-pic-frontend && npx tsc --noEmit --pretty false` passed.
- Re-ran `cd ai-pic-frontend && npm run lint`; it passed with the same 3 existing warnings listed above.
- Re-ran `cd ai-pic-frontend && npm run build`; it passed.
- `cd ai-pic-backend && pytest tests/test_timeline_clip_keyframe_api.py tests/test_timeline_clip_keyframe_processor.py tests/test_timeline_clip_video_rework_context_api.py -q` passed: 4 tests.
- `cd ai-pic-backend && python run_tests.py quick` did not reach tests because dependency installation failed in this Python 3.13 environment: `langchain-core==0.2.43` requires `pydantic>=2.7.4`, while the repo pins `pydantic==2.5.0`.
- `git diff --check` passed.
- Chrome DevTools validation was attempted first and failed because `http://127.0.0.1:9222/json/version` returned HTTP Not Found.
- Browser fallback used Playwright with system Chrome, not Chrome DevTools. Evidence:
  - `artifacts/runs/storyboard-clip-management-2026-06-09T14-01-52-109Z/storyboard-clip-management.png`
  - `artifacts/runs/storyboard-clip-management-2026-06-09T14-01-52-109Z/timeline-clip-management.png`
  - `artifacts/runs/storyboard-clip-management-2026-06-09T14-01-52-109Z/browser-validation.json`
- Fallback path verified:
  - Opened `/episodes/340cacb9ed854bb18d50f2c69547bf03/workspace?tab=storyboard&scriptId=142`.
  - Found `片段分镜管理`, `环境/IP 待绑定`, and `进入分镜管理`.
  - Clicked the management link to `/episodes/340cacb9ed854bb18d50f2c69547bf03/workspace?tab=timeline&scriptId=142&clipId=video_scene_577_beat_3886_001`.
  - Found `片段分镜管理`, `故事板参考`, and the `生成故事板参考图` button on the Timeline tab.
  - Console contained React DevTools info and a local Next HMR WebSocket 404 only.
- Re-ran browser fallback for the video binding summary. Evidence:
  - `artifacts/runs/video-binding-context-2026-06-09T14-12-55-716Z/video-binding-context.png`
  - `artifacts/runs/video-binding-context-2026-06-09T14-12-55-716Z/browser-validation.json`
- Video binding fallback path verified:
  - Opened `/episodes/340cacb9ed854bb18d50f2c69547bf03/workspace?tab=timeline&scriptId=142&clipId=video_scene_577_beat_3886_001`.
  - Found `视频生成绑定上下文` inside the video card.
  - The current runtime clip had no selectable IP/environment image buttons, so the card correctly displayed `角色 IP：未绑定`, `IP 图：0 张`, `环境图：0 张`, and `先在上方故事板参考里绑定角色 IP 和环境图，视频任务会一并携带。`.
- Re-ran browser fallback for the full clip production sequence. Evidence:
  - `artifacts/runs/clip-keyframes-flow-2026-06-09T14-28-16-445Z/clip-keyframes-flow.png`
  - `artifacts/runs/clip-keyframes-flow-2026-06-09T14-28-16-445Z/browser-validation.json`
- Full clip production fallback path verified:
  - Opened `/episodes/340cacb9ed854bb18d50f2c69547bf03/workspace?tab=timeline&scriptId=142&clipId=video_scene_577_beat_3886_001`.
  - Found `故事板参考`, `生成首尾帧`, `视频生成绑定上下文`, and `生成/重做此片段视频` in the selected clip production flow.
  - Chrome DevTools was attempted first and still failed because `http://127.0.0.1:9222/json/version` returned HTTP Not Found, so evidence used Playwright with system Chrome.
- Re-ran browser fallback for the missing video IP/environment binding complaint. Evidence:
  - `artifacts/runs/video-binding-env-ip-2026-06-09T14-43-56-555Z/timeline-video-binding.png`
  - `artifacts/runs/video-binding-env-ip-2026-06-09T14-43-56-555Z/browser-evidence.json`
- Video IP/environment binding fallback path verified:
  - Opened `/episodes/340cacb9ed854bb18d50f2c69547bf03/workspace?tab=storyboard&scriptId=142`.
  - Clicked `进入分镜管理` to `/episodes/340cacb9ed854bb18d50f2c69547bf03/workspace?tab=timeline&scriptId=142&clipId=video_scene_577_beat_3886_001`.
  - Found the clip-level `片段环境` selector even though the clip has no matched normalized scene.
  - The selector had 13 options; selected `办公室`.
  - Environment detail request `/api/v1/story-structure/environments/1` returned 200 and loaded environment thumbnails.
  - Clicked `选择环境图 办公室 1`; the video card changed to `已携带绑定` and `环境图：1 张`.
  - The same card showed `暂无角色 IP，请先在临时角色绑定 VirtualIP。` and the `去临时角色绑定 IP` action because the runtime endpoint `/api/v1/episodes/163/characters?page=1&page_size=20` returned 200 with no character rows.
  - Console contained React DevTools info and local Next HMR WebSocket 404 only.
- Commit-prep validation:
  - `pre-commit run --files <changed files>` reformatted Python/TypeScript files via Black and Prettier, then stopped at the backend quick hook because full backend collection still has unrelated baseline import errors:
    - `cannot import name '_BEAT_CONTRACT_MAX_TOKENS' from 'app.services.ai.scripts_ai_manager'`
    - `cannot import name 'structured_script_score' from 'scripts.harness.production_quality_script'`
    - `cannot import name 'STRUCTURED_SCORE_PASS' from 'scripts.harness.production_quality_script'`
  - After hook formatting, `cd ai-pic-backend && pytest tests/test_timeline_clip_keyframe_api.py tests/test_timeline_clip_keyframe_processor.py tests/test_timeline_clip_video_rework_context_api.py -q` passed: 4 tests.
  - After hook formatting, `cd ai-pic-frontend && npm run test` passed: 53 tests.
  - After hook formatting, `cd ai-pic-frontend && npm run lint` passed with the same 3 existing warnings listed above.
  - After hook formatting, `cd ai-pic-frontend && npm run build` passed.
  - `SKIP=backend-pytest pre-commit run --files <changed files>` passed all remaining hooks; `backend-pytest` was explicitly skipped because of the unrelated baseline collection import errors above.
  - `python scripts/check_repo_docs.py` passed.
  - `python scripts/check_repo_contracts.py --mode audit` passed.
  - `python scripts/check_repo_contracts.py --mode diff <changed and untracked files>` passed.
  - `git diff --check` passed.
  - `./docker/build_prod_images.sh` passed and pushed:
    - `registry.cn-beijing.aliyuncs.com/geyunfei/ai-video-backend:a04c0fa5`
    - `registry.cn-beijing.aliyuncs.com/geyunfei/ai-video-frontend:a04c0fa5`

## Next Steps

- Runtime clip `video_scene_577_beat_3886_001` now has selectable environment images after choosing a clip environment.
- Runtime episode 163 still has no角色 IP rows, so IP image binding requires creating or binding a VirtualIP under `临时角色` first.

## Linked Commits

- Pending.
