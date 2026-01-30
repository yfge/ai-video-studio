---
id: 2025-12-13T12-40-57Z-style-spec-image-flows
date: 2025-12-13T12:40:57Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, style, image_generation]
related_paths:
  - ai-pic-backend/app/api/v1/ai_providers.py
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/app/utils/style_utils.py
summary: "Propagated StyleSpec through txt2img/img2img flows and persisted resolved style metadata."
---

## User Prompt

统一改动全部文生图/图生图结点：后端作为唯一真源，支持 13 维 StyleSpec + 预设（写死在代码里、全局统一），前端可按场景只传部分字段；旧 style 仍需兼容，并把风格信息落库便于追溯。

## Goals

- 为所有 txt2img/img2img 调用链增加 `style_preset_id` + 可选 `style_spec`（partial）参数。
- 后端统一 resolve：`preset/defaults + overrides + legacy style fallback`，并做 provider 级参数映射。
- 在关键业务对象上持久化 resolved 风格信息，保证可审计/可复现。
- 不中断现有只传 `style` 的调用（兼容旧 UI/旧 worker）。

## Changes

- `AIServiceManager.generate_image` / `AIServiceManager.image_to_image` 支持 `style_preset_id` 与 `style_spec`，并：
  - resolve 为完整 `StyleSpec`（补齐 defaults/preset）
  - 追加稳定 prompt 后缀（`STYLE_SPEC => ...`）
  - 推导 legacy `style`（realistic/anime/cartoon/portrait）与 OpenAI `style`（natural/vivid）
  - 将 resolved spec 写入 `AIResponse.metadata.style_spec` + `style_spec_resolution`
- 虚拟 IP 文生图/图生图：
  - API payload 透传 `style_preset_id/style_spec`
  - 将 resolved spec 写入 `VirtualIPImage.generation_params`（JSON）用于追溯
- 环境资产文生图/图生图：
  - API payload 透传 `style_preset_id/style_spec`
  - 将 resolved spec 写入 `Environment.extra_metadata.last_*_generation`
- 分镜图片生成（script storyboard images）：
  - 请求支持 `style_preset_id/style_spec`
  - Celery payload 透传并在生成后写入 `script.extra_metadata.storyboard.meta` 便于前端展示/复现

## Validation

- Backend lint/format:
  - `cd ai-pic-backend && ruff check ...`（仅本次改动文件）
  - `cd ai-pic-backend && black --check ...`（仅本次改动文件）
- Backend targeted test:
  - `cd ai-pic-backend && pytest -q tests/test_story_structure_endpoints.py::test_environment_variants_pass_reference_images`
- Chrome E2E (localhost:8089):
  - 登录账号 `geyunfei`
  - 打开 `http://localhost:8089/environments`，点击「办公室」任一参考图打开「环境图生图」弹窗
  - 点击「提交图生图任务」，提示「已创建环境图变体任务」
  - 跳转 `http://localhost:8089/tasks`，确认新任务出现在列表顶部且状态可见

## Next Steps

- 前端接入后端 styles schema/presets（下拉选择预设 + 按页面只传部分 `style_spec`）。
- 增加单元测试覆盖：resolve 逻辑、prompt 注入、provider style 映射、持久化字段。
- 补齐更多 provider 的 style 参数映射（如有差异化字段）。

## Linked Commits

- feat(backend): apply style spec across image flows
