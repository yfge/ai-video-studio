## User Prompt

用户要求实现“分镜内故事板”计划，并明确“故事板”是在选中分镜内的操作，不是整剧或整条 Timeline 生成一个故事板。

## Goals

- 将故事板生成改为 Timeline `video` clip 级操作。
- 废弃新的整 Timeline `storyboard-grid/generate` 生成入口。
- 新增 clip-scoped API、payload、spec 写回、asset lineage 和 rework reference mode。
- 前端只在选中 video clip inspector 内提供“生成故事板”和“使用故事板参考生成视频”，Storyboard tab 不再提供整页生成入口。
- 保留旧 `storyboard_grid` / `storyboard_grid_panel` 数据为 legacy read path。

## Changes

- 后端新增 `POST /api/v1/timelines/{timeline_id}/clips/{clip_id}/storyboard/generate`，验证 version、clip 存在和 video 类型后，只为选中 `clip_id` 排 `timeline_clip_storyboard` 任务。
- 后端旧 `POST /api/v1/timelines/{timeline_id}/storyboard-grid/generate` 改为返回 410 deprecation/gone 错误。
- clip storyboard processor 只写选中 clip 的 `source_refs.clip_storyboard`、`clip_storyboard_sheet_asset_ref` 和 `support_views.clip_storyboards[clip_id]`，并同步 `clip_storyboard_sheet` lineage。
- provider-backed video rework 新增 `clip_storyboard_panel` / `use_clip_storyboard` 路径，reference-only storyboard sheet 仍按 image-to-video 分类提交；旧 `storyboard_grid_panel` 保持 legacy 接受。
- 前端 timeline API client 新增 `generateTimelineClipStoryboard`，移除旧 timeline-level grid generation client export。
- 前端 Timeline clip inspector 增加 clip storyboard 生成控件、sheet 预览和 `clip_storyboard_panel` rework payload；Storyboard tab 移除 whole-Timeline 生成 UI。
- 更新 `docs/exec-plans/active/grid-storyboard-mode.md`、`docs/timeline-rendering-pipeline.md`、`tasks.md`，明确故事板是 clip-scoped support asset。
- 新增/更新 targeted backend/frontend tests 覆盖 stale version、missing/non-video clip、selected clip-only 写回、clip storyboard rework、frontend endpoint 和 Storyboard tab 行为。

## Validation

- Passed: `git diff --check`.
- Passed: `cd ai-pic-frontend && PATH=/Applications/Codex.app/Contents/Resources:$PWD/node_modules/.bin:$PATH node_modules/.bin/eslint .` with 0 errors and 19 warnings.
- Passed: `cd ai-pic-frontend && PATH=/Applications/Codex.app/Contents/Resources:$PWD/node_modules/.bin:$PATH node_modules/.bin/tsx --test tests/timelineApiEndpoints.test.ts tests/timelineClipReworkControls.test.ts tests/workspaceStoryboardTabContent.test.tsx` with 10 tests passing.
- Passed: `cd ai-pic-frontend && PATH=/Applications/Codex.app/Contents/Resources:$PWD/node_modules/.bin:$PATH node_modules/.bin/tsx --test $(find tests -type f \( -name '*.test.tsx' -o -name '*.test.ts' -o -name '*.test.js' \))` with 38 tests passing.
- Passed: `cd ai-pic-frontend && PATH=/Applications/Codex.app/Contents/Resources:$PWD/node_modules/.bin:$PATH node_modules/.bin/tsc --noEmit`.
- Passed: backend syntax-only `ast.parse` over 16 touched backend Python source/test files.
- Blocked: backend targeted pytest command remained silent for 45 seconds and was terminated: `cd ai-pic-backend && .venv/bin/pytest tests/test_timeline_storyboard_grid_api.py tests/test_timeline_storyboard_grid_processor.py tests/test_timeline_clip_video_grid_rework_api.py tests/unit/services/video/test_timeline_clip_video_rework_submission.py -q`.
- Blocked: `python3 scripts/check_repo_docs.py` remained silent for 45 seconds and was terminated.
- Blocked: `python3 scripts/check_repo_contracts.py --mode diff $(git diff --name-only)` remained silent for 30 seconds and was terminated.
- Blocked: `node_modules/.bin/next build` remained silent for 60 seconds and was terminated; `tsc --noEmit` was used as compile fallback.
- Blocked: browser validation. `http://localhost:8089/` responded, but `POST /api/v1/auth/login` remained silent beyond its timeout window and was terminated. Evidence note: `artifacts/runs/clip-storyboard-scope-20260604T050423Z/browser_validation.json`.

## Next Steps

- Re-run backend pytest, repo docs/contracts checks, Next build, and the real browser flow after the local Python/API environment stops hanging.
- Browser flow still needs a logged-in operator workspace pass that selects a video clip, submits `/clips/{clip_id}/storyboard/generate`, and confirms no call to the old `/storyboard-grid/generate` endpoint.

## Linked Commits

None yet.
