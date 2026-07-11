## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交；先提交现有变更。

## Goals

- 让人工选用的视频通过显式操作写入绑定的 stable `clip_id`。
- 使用 Timeline 乐观版本控制，禁止静默覆盖并保留媒体 lineage。
- 保持候选节点自己的剧本上下文，避免后续节点覆盖候选资产查询范围。

## Changes

- 增加画布视频 Timeline placement API 和独立服务，校验 approved video、目标 Timeline、stable clip 与 expected version。
- 复制并更新 Timeline spec，把选中视频资产写入目标 video clip，关闭 placeholder，并由 Timeline 服务生成新版本和 `generated_video` lineage。
- 回写画布节点的新 Timeline version、placed clip 与 media asset，支持刷新恢复和重复操作冲突检测。
- 在视频候选卡片增加显式“放入 Timeline”操作和已落位状态。
- 修复共享画布上下文覆盖候选节点已绑定 `script_id` 的问题，并增加回归测试。
- 增加集成测试，覆盖选片、落位、稳定 clip、lineage 与 stale version 409。

## Validation

- `cd ai-pic-backend && pytest tests/integration/test_production_canvas_candidate_review_api.py -q`：2 passed。
- `cd ai-pic-frontend && npx tsx --test tests/productionCanvasState.test.ts tests/productionCanvasPlanner.test.tsx`：14 passed。
- `cd ai-pic-backend && pytest -q`：2445 passed，88 skipped。
- `cd ai-pic-frontend && npm run test`：290 passed。
- `cd ai-pic-frontend && npm run lint`：0 errors，3 个既有 warnings。
- `cd ai-pic-frontend && npm run build`：Next.js production build 通过。
- `python scripts/check_repo_docs.py`：通过。
- `python scripts/check_repo_contracts.py --mode diff ...`：通过。
- `pre-commit run --files <本提交文件>`：全部通过，包含 backend quick gate 与 frontend lint。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：后端与前端生产镜像构建成功，未推送。

## Next Steps

- 完成图片候选到视频再到 Timeline 的内置浏览器全链路证据归档。
- 补齐视频任务进度、失败重试相关交互。

## Linked Commits

- This commit
