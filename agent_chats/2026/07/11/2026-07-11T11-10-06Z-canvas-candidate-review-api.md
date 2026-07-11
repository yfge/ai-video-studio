## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 为图片和视频候选建立后端持久资产与显式人工选用契约。
- 让 selected output 成为类型化图执行的真实输入，并在变化时传播 stale。
- 继续复用现有 storyboard、media asset 和 Run 保存链路。

## Changes

- 新增画布节点候选查询与选用 API，从现有 storyboard 历史提取媒体并幂等注册为 `media_assets`。
- 保存节点新增选中资产、URL、审核人和审核时间字段；选用时写回对应 `approved_image` 或 `approved_video` 输出。
- 选用操作递增源节点定义版本并更新其当前输入指纹，使已消费旧选用结果的下游节点变为 stale，而源节点保持 approved。
- Run 保存切换为 Pydantic JSON 模式，支持审核时间等标准 JSON 类型。
- 更新 `tasks.md`，将已经完成的 stale descendants 标为完成，保留候选 UI 和 Timeline 回填为未完成。

## Validation

- `pytest -q tests/integration/test_production_canvas_candidate_review_api.py tests/integration/test_production_canvas_media_api.py tests/unit/test_production_canvas_stale_runtime.py tests/unit/test_production_canvas_graph_runtime.py`：6 passed。
- `cd ai-pic-backend && pytest -q`：2443 passed，88 skipped。
- `python scripts/check_repo_contracts.py --mode diff ...`：通过。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：前后端生产镜像本地构建通过，未推送。
- `python run_tests.py quick`：未进入测试；本机 Python 3.13 下仓库固定 `pydantic==2.5.0` 与 `langchain-core` 依赖解析冲突，改用直接 `pytest` 全量验证。

## Next Steps

- 在画布节点内展示候选图片/视频、选中状态和显式选用操作。
- 将 approved video 通过 stable `clip_id` 和 Timeline version 显式回填。

## Linked Commits

- This commit
