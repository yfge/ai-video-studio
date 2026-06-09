## User Prompt

分镜/故事板生成入口还是有问题，没有绑定角色参考 图，没有生成的选择！！ 整体链路是 TMD 乱的

## Goals

- Keep storyboard generation clip-scoped from the selected Timeline video clip production panel.
- Bind available character/environment reference context into clip storyboard generation payloads.
- Add explicit video reference-source choices so generated storyboard panels and manual reference images are visible inputs.
- Validate backend payload construction, frontend controls, contracts, and browser-visible workflow.

## Changes

- Added clip storyboard context assembly that merges explicit user references with Timeline, speaker, story-character, and environment hints before queuing provider work.
- Added a repository for story character visual lookup so storyboard services do not reach directly into SQLAlchemy queries.
- Annotated storyboard task panels and task parameters with bound context and deduplicated reference images.
- Split the frontend clip production controls into storyboard reference and video reference sections.
- Added video reference choices for `首尾帧`, `故事板 Panel`, and `手动参考图`, with manual reference URL parsing shared across storyboard and video queue payloads.
- Added focused backend and frontend tests for context binding and reference-source payloads.

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/storyboard/test_clip_storyboard_context.py tests/test_timeline_storyboard_grid_api.py tests/test_timeline_clip_storyboard_context_api.py -q`
  - Passed: 9 tests.
- `cd ai-pic-frontend && npx tsx --test tests/timelineClipReworkControls.test.ts`
  - Passed: 8 tests.
- `cd ai-pic-frontend && npm run test`
  - Passed: 42 tests.
- `cd ai-pic-frontend && npm run lint`
  - Passed with existing warnings for anonymous default export and existing image tags.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/repositories/story_character_visual_repository.py ai-pic-backend/app/services/storyboard/clip_storyboard_context.py ai-pic-backend/app/services/storyboard/clip_storyboard_environment_context.py ai-pic-backend/app/services/storyboard/grid_storyboard_sheet_service.py ai-pic-backend/app/services/storyboard/storyboard_audio_character_visuals.py ai-pic-backend/tests/test_timeline_clip_storyboard_context_api.py ai-pic-backend/tests/unit/services/storyboard/test_clip_storyboard_context.py ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkCardSections.tsx ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkCards.tsx ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControls.tsx ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkModel.ts ai-pic-frontend/src/utils/api/types/timeline.types.ts ai-pic-frontend/tests/timelineClipReworkControls.test.ts`
  - Passed.
- `pre-commit run --files ...`
  - Black/prettier reformatted scoped files, then the broad `backend-pytest` hook failed on existing collection/import drift outside this change: `_BEAT_CONTRACT_MAX_TOKENS`, `structured_script_score`, and `STRUCTURED_SCORE_PASS` are missing from unrelated script-quality modules.
- `SKIP=backend-pytest pre-commit run --files ...`
  - Passed for merge-conflict checks, whitespace, ruff, black, isort, prettier, repo docs, repo contracts, ledger enforcement, and frontend lint.
- `./docker/build_prod_images.sh`
  - Attempted after Docker availability was confirmed with `docker info --format '{{.ServerVersion}}'` returning `28.3.2`.
  - The script remained as `bash ./docker/build_prod_images.sh` for several minutes with no child Docker build/buildx process and no emitted script output, so the stuck local validation attempt was stopped before commit.
- Chrome DevTools validation was attempted first and failed because `http://127.0.0.1:9222/json/version` returned HTTP Not Found.
- Playwright fallback with system Google Chrome passed against `http://localhost:8089/episodes/6/workspace?tab=timeline&scriptId=8`.
  - Evidence: `artifacts/runs/storyboard-entry-fallback-20260609T082631Z/browser_evidence.json`
  - Screenshot: `artifacts/runs/storyboard-entry-fallback-20260609T082631Z/timeline-production-panel.png`
  - Assertions passed for `选中片段生产`, `片段生成`, `生成故事板参考图`, `附加参考图 URL`, and `视频参考来源`.
  - Reference options observed: `首尾帧`, `故事板 Panel`, `手动参考图`.
  - Non-blocking console message: local Next HMR WebSocket returned 404 through nginx; no page errors.

## Next Steps

- After a storyboard panel image is actually produced by the async task, use the enabled `故事板 Panel` choice to queue video generation from the generated panel.
- Confirm real provider output quality separately if model/provider credentials and worker runtime are available.

## Linked Commits

- None yet.
