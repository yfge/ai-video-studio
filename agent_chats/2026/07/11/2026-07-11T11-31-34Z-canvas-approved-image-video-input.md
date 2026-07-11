## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 让 `approved_image -> start_frame` 类型化边改变真实视频候选请求。
- 禁止视频队列静默退回 storyboard 最新图覆盖人工选用结果。
- 避免把一个选用图片误绑定到多个目标镜头。

## Changes

- 画布执行请求增加显式 `start_frame_url`，图运行时从 selected output 解析并写入该字段。
- 视频候选服务把解析后的起始帧传给现有 storyboard 视频队列。
- 队列在存在显式起始帧时覆盖默认候选 selection，并要求恰好一个 frame index；不满足时返回可解释 blocked 状态。
- 视频节点执行输出记录实际 `start_frame_url`，便于审核与恢复。
- 增加图解析单元测试和媒体 API 集成断言，证明视频任务 payload 使用人工选用图片。

## Validation

- `pytest -q tests/unit/test_production_canvas_graph_runtime.py tests/integration/test_production_canvas_media_api.py tests/integration/test_production_canvas_candidate_review_api.py`：6 passed。
- `cd ai-pic-backend && pytest -q`：2444 passed，88 skipped。
- `python scripts/check_repo_contracts.py --mode diff ...`：通过。
- `python scripts/check_repo_docs.py`：通过。
- `pre-commit run --files <本提交 7 个文件>`：全部通过，包含 backend quick gate；frontend lint 因无前端文件而跳过。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：后端与前端生产镜像构建成功；classic builder 仍报告已有日志文件归档 warning，但未影响构建结果。
- 未在浏览器触发真实视频任务，避免产生 provider 调用费用；上一提交的内置浏览器证据已证明 approved image 与 selected-output 边持久化。

## Next Steps

- 展示并人工选用已有视频候选，验证 `approved_video`。
- 将 approved video 通过 stable `clip_id` 和 Timeline version 显式回填。

## Linked Commits

- This commit
