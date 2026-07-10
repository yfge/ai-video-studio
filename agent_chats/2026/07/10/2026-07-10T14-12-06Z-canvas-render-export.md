# Canvas Render Export

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- 在生产画布内补齐可执行的 Render 和 Export 节点。
- 让旧 Canvas run 无需重建即可获得新节点，并保存 RenderJob 证据。
- 将可见主链调整为 Timeline-first，并在 dev 内置浏览器验证最终成片出口。

## Changes

- 新增 `timeline.render`，在所有 Timeline clips 可解析后幂等创建当前版本的 final RenderJob；失败或取消的同 preset job 会创建新 attempt。
- 新增 `timeline.export`，读取当前 Timeline/version 的 final RenderJob，并在成功后暴露 output asset 和下载 URL。
- Canvas skill 清单和节点位置改为 Timeline 先于 storyboard/image/video，Render 和 Export 位于视频候选之后。
- 旧 run 读取时按当前 skill manifest 补齐缺失节点，并从 saved state 恢复 script/Timeline 上下文；前端恢复会保留旧布局并追加新 plan nodes。
- RenderJob 在画布中生成独立 `Render #<id>` 证据节点，成功成片会显示可点击的“打开成片”。
- 顶部生产链摘要更新为 `Audio + Timeline -> Storyboard Support -> ... -> Render -> Export`。

## Validation

- Backend targeted: production canvas plan/registry/render/media integration tests passed.
- `cd ai-pic-backend && python run_tests.py quick --no-setup`: 2411 passed, 77 skipped, 20 deselected.
- `cd ai-pic-backend && python -m pytest -q`: 2421 passed, 88 skipped.
- `cd ai-pic-frontend && npm run lint`: passed with 0 errors and 3 existing warnings.
- Frontend focused Canvas suites: 31 passed.
- Frontend suite excluding the unrelated hanging `toastProvider.test.tsx`: 248 passed.
- Full `npm run test` was attempted; `toastProvider.test.tsx` passed its assertion but the Node runner timed the dirty WIP file out after 273 seconds.
- Dev run `48d62cd56e1646c4b3f0c77c1a3cd4a6` restored Render/Export nodes without rebuilding the run.
- In-app browser executed Render Skill and reused succeeded render #122 for Timeline 71 v6, then executed Export Skill and exposed output asset #375 plus the final MP4 link.
- Reload preserved both skill nodes and two `Render #122` evidence nodes in run task #6266; MySQL JSON paths confirmed both skills under `saved_state`.
- Browser Console contained no warnings or errors. Screenshot: `artifacts/runs/canvas-render-export-20260710T1400Z/canvas-render-export-122.jpg`.
- `python scripts/check_repo_docs.py` and scoped repository contracts: passed.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`: backend and frontend production images built locally without push; Next.js production build passed.

## Next Steps

- Add native polling for RenderJob evidence so a newly queued render transitions to export-ready without a second manual node execution.
- Continue reconciling the remaining uncommitted Canvas interaction refactor as separate atomic slices.

## Linked Commits

- `a5fc9272` - `fix(canvas): bind video batches to timeline clips`
- This commit (pending)
