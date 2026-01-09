---
id: 2026-01-09T11-54-18Z-storyboard-image-gen-normalization
date: "2026-01-09T11:54:18Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image, storyboard, refactor]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/services/storyboard/storyboard_image_generation.py
  - ai-pic-backend/tests/unit/services/storyboard/test_storyboard_image_generation.py
summary: "Phase 4 (WIP): route storyboard image generation through image-gen normalization + provider-safe kwargs"
---

## User Prompt

用户要求对「虚拟 IP 图生图、环境文生图/图生图、分镜图生图」进行统一梳理并落地，提升图像生成质量一致性；继续推进 Phase 4（分镜链路接入统一归一化层）。

## Goals

- 分镜图像生成统一接入 `normalize_image_gen_request` + `build_ai_manager_call`，避免在 endpoint 内散落 provider/model/size/aspect_ratio/extra_images 透传逻辑。
- 保持现有分镜锚点参考图合并策略与 prompt 生成逻辑不变，仅收敛“调用 AIManager 的参数构建”。

## Changes

- 新增 `generate_storyboard_image_urls` 服务：`ai-pic-backend/app/services/storyboard/storyboard_image_generation.py`
  - 统一构建 `ImageGenRequest(domain=STORYBOARD)` 并调用归一化层与 provider-safe 参数过滤
  - 统一解析响应 `image_url/url/images[]` 并返回 `{urls, provider, model, style_spec...}`
- 分镜生成端点内 `_gen_images(...)` 改为委托到上述 service（保留 `_abs_url` 规则以保证容器内可访问 URL）：`ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`
- 新增单元测试覆盖 txt2img/img2img 两条路径的参数过滤与 extra_images 行为：`ai-pic-backend/tests/unit/services/storyboard/test_storyboard_image_generation.py`

## Validation

- Unit tests:
  - `pytest -q tests/unit/services/storyboard/test_storyboard_image_generation.py`
- Chrome E2E（Docker dev + Nginx，`http://localhost:8089`）：
  1. 登录：`geyunfei` / `Gyf@845261`
  2. 打开分镜页：`/episodes/8/storyboard`
  3. 在分镜帧 7 的「关键帧预览」区域点击「图生图」
  4. 在弹窗中选择提供商/模型：`火山引擎` → `Seedream 4.5`，将「生成张数」改为 `1`，点击「提交图生图任务」
  5. 弹窗提示「操作成功：已创建图像生成任务」
  6. 跳转到任务页：`/tasks`，确认创建任务成功并已完成：`分镜图像生成 - LangGraph 全链路回归测试 / 第2集 共鸣与冲突`（Task ID: 544），在「详情」中可看到 `model=volcengine:doubao-seedream-4-5-251128`、`count=1` 等参数

## Next Steps

- 将分镜链路的归一化审计信息（如 dropped_fields、refs hash、warnings）写入 Task.parameters / storyboard metadata，提升可追溯性（按设计文档）。

## Linked Commits

- TBD
