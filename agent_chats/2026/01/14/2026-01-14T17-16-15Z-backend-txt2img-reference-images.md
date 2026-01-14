---
id: 2026-01-14T17-16-15Z-backend-txt2img-reference-images
date: 2026-01-14T17:16:15Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, providers]
related_paths:
  - ai-pic-backend/app/services/image_gen/provider_params.py
  - ai-pic-backend/tests/unit/services/image_gen/test_provider_params_reference_images.py
summary: "Pass reference_images through provider-safe txt2img payloads"
---

## User Prompt
全局检查文生图/图生图提示词规范；确认模板语义与 provider 参数一致性；并按 provider 做进一步优化，原子化分布提交。

## Goals
- 修复文生图请求中 reference_images 丢失的问题（为后续 provider 参考图能力铺路）。
- 增加单测覆盖，避免回归。
- 保持改动原子化、可验证。

## Changes
- `build_ai_manager_call()` 在 `text_to_image` 模式下补齐 `reference_images`（来自标准化后的 `normalized.extra_images`）。
- 新增单测覆盖 Google/Volcengine 文生图场景下 `reference_images` 的透传。

## Validation
- Backend unit: `cd ai-pic-backend && pytest tests/unit/services/image_gen/test_provider_params_reference_images.py -q`
- Docker: `./docker/build_prod_images.sh`
- Chrome E2E (MCP):
  - 登录 `geyunfei` 后进入 `http://localhost:8089/environments/aab17f172446462a97e738772337d272`
  - 在「AI 生成参考图」填写补充提示词并点击「创建生成任务」，确认弹窗
  - DevTools Network: `POST /api/v1/story-structure/environments/.../images/generate-async` (reqid=748, 200)

## Next Steps
- 将 `ui_metadata.py` 的 provider 提示（如 negative_prompt 不支持）改为按能力自动生成，覆盖 jimeng 等 provider。
- 评估是否在文生图 UI 增加 reference images 输入（按 provider/model 动态展示）。

## Linked Commits
- (pending)
