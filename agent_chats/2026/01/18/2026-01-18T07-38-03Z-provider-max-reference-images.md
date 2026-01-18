---
id: 2026-01-18T07-38-03Z-provider-max-reference-images
date: 2026-01-18T07:38:03Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, frontend, image-gen]
related_paths:
  - ai-pic-backend/app/services/image_gen/ui_metadata.py
  - ai-pic-backend/tests/unit/services/image_gen/test_ui_metadata_reference_images.py
  - ai-pic-frontend/src/components/shared/modals/image-to-image/useReferenceSelection.ts
  - ai-pic-frontend/src/components/features/environments/EnvironmentGenerationFields.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentReferenceImagesField.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationForm.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/VirtualIPReferenceImagesField.tsx
  - ai-pic-frontend/src/utils/modelUi.ts
  - tasks.md
summary: "Expose provider max reference images and enforce selection limits in image-gen UIs."
---

## User Prompt

- 全局检查文生图/图生图提示词规范，确认模板语义是否合适、是否与各 provider 参数一致，并可按 provider 进一步优化。
- 优化所有 provider 和域；参考现有形式，在选择不同 provider 时动态加载输入以得到额外信息；原子化分布提交。
- 检查并更新 `tasks.md`。

## Goals

- 让前端能从后端模型元数据获取“参考图张数上限”，避免 UI 允许选择过多参考图导致 provider 侧失败（例如 Gemini 413）。
- 在环境/虚拟 IP/分镜等入口对 `reference_images` 做一致的上限约束与提示。

## Changes

- Backend: 在 `image_gen` UI metadata 中为文生图补充 `max_reference_images`（Google=4、可灵=1），并新增单元测试覆盖。
- Frontend:
  - 解析后端 `max_reference_images` → `maxReferenceImages`。
  - 在 `ImageToImageModal` 的参考图选择逻辑里基于 `maxReferenceImages` 自动裁剪。
  - 在环境/虚拟 IP 的文生图参考图选择器中显示上限提示，并在选择时自动裁剪（超过上限替换最早选择）。
- Docs/Tasks: 更新 `tasks.md`，补充已完成事项。

## Validation

- Backend: `cd ai-pic-backend && pytest -q tests/unit/services/image_gen/test_ui_metadata_reference_images.py tests/unit/services/image_gen/test_ui_metadata_negative_prompt_notes.py`
- Frontend: `cd ai-pic-frontend && npm run lint`（0 errors）
- Docker: `./docker/build_prod_images.sh`（脚本使用 tag `84353d5`）
- Chrome E2E (MCP):
  - 登录 `geyunfei` 后进入环境详情页 `http://localhost:8089/environments/5da63b15b5a640b380ef22cc30dc192b`
  - Google：提示显示“最多 4 张”，脚本连续点击 5 张参考图后，选中数保持为 4（自动替换最早选择）
  - 可灵：切换 provider 为“可灵”后提示显示“最多 1 张”，脚本连续点击 2 张参考图后，选中数保持为 1

## Next Steps

- 根据各 provider 官方限制，补齐更多 `max_reference_images`（以及 img2img 的 extra_images 上限）并在 UI 侧统一展示。
- 将同一套上限约束覆盖到分镜文生图 references（当引用图源可用且 UI 提供选择时）。

## Linked Commits

- (pending) feat(image-gen): enforce provider reference image limits
