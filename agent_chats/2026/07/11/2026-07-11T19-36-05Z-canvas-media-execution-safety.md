## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交；先提交现有变更。

## Goals

- 限制未指定帧的候选生成范围，避免一次画布操作意外生成整套分镜媒体。
- 让图片 worker 在持久化取消后尽快停止后续昂贵阶段和帧处理。
- 禁止未生成并持久化任何图片的任务报告成功。

## Changes

- 图片和视频候选请求未显式指定帧时默认使用首帧 `[0]`；基于候选分支的执行仍使用候选自身帧索引。
- 图片 worker 在开始、动态提示词后、逐帧前、保存前和状态落库前重新读取取消状态。
- 图片 worker 仅在至少一个目标帧返回持久化媒体后完成，否则写入失败状态和明确错误。
- 增加默认单帧、启动前取消、帧间取消和空媒体失败测试，并用有效的内联 PNG 覆盖持久化测试。
- 更新无限画布设计文档和任务板中的媒体执行安全契约。

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_storyboard_image_task_image_gen_persistence.py tests/unit/test_storyboard_image_task_safety.py tests/integration/test_production_canvas_media_api.py tests/integration/test_production_canvas_media_defaults.py tests/unit/test_production_canvas_skill_plan.py -q` -> 14 passed。
- `python scripts/check_repo_docs.py` -> 通过。
- `python scripts/check_repo_contracts.py --mode diff <本次路径>` -> 通过；新增测试已拆分到独立模块，所有 Python 文件低于 300 行硬限制。
- scoped `pre-commit run --files <本次路径>` -> 通过，包含 backend quick gate。
- `./docker/build_prod_images.sh` -> backend/frontend `linux/amd64,linux/arm64` 构建并推送成功；frontend `/canvas` production route 构建通过。
- 内置浏览器：`http://localhost:8089/canvas?run_id=9a4bbfdb95f846e4be216beb1b09ad88`。
- 浏览器路径：选择 Image Candidates，清空帧索引并取消“要求参考图”，运行节点；服务端创建任务 `6323`。
- DB：任务 `6323` 为 `COMPLETED`，参数 `frame_indexes=[0]`、`require_reference_images=false`；Script `30` 的首帧持久化 URL 为 `https://resource.lets-gpt.com/ai-generated/storyboard/image/20260711/193423/b21c0937.png`。
- UI：任务 `6323` 显示已完成，媒体帧索引回显为 `0`；Console warning/error 为空。
- 候选评审区刷新后显示帧 1 图片、原始资产链接和“从此分支 / 拒绝 / 选用”操作。
- 并行运行两套 pytest 曾争用共享 `test.db` 并产生 `attempt to write a readonly database`；清理临时库并串行重跑后，定向用例和 backend quick gate 均通过。

## Next Steps

- 在同一 Run 评审并选用图片候选，继续 provider-backed 视频候选、选片和 Timeline 回填。
- 单独修复 Run Ready/Resume 跳过 `skill_result` 可执行节点的问题。

## Linked Commits

- This commit.
