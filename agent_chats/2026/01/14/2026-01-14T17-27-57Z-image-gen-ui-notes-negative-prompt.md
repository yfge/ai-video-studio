---
id: 2026-01-14T17-27-57Z-image-gen-ui-notes-negative-prompt
date: 2026-01-14T17:27:57Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, ui]
related_paths:
  - ai-pic-backend/app/services/image_gen/ui_metadata.py
  - ai-pic-backend/tests/unit/services/image_gen/test_ui_metadata_negative_prompt_notes.py
summary: "Generate negative_prompt warnings from provider capabilities"
---

## User Prompt

全局检查文生图/图生图提示词规范与 provider 参数一致性；根据 provider 做进一步优化，并原子化分布提交。

## Goals

- provider 切换时，UI 能稳定展示「不支持 negative_prompt」等关键信息（按能力自动推导，而非硬编码 provider 白名单）。
- 增加单测覆盖，防止回归。

## Changes

- `build_image_gen_ui_metadata()`：当 `supports_negative_prompt == false` 时，自动在对应 mode 的 `notes` 里追加提示；并保留可灵图生图专用提示文案。
- 新增单测覆盖 jimeng img2img 提示与 keling 专用提示。

## Validation

- Backend unit: `cd ai-pic-backend && pytest tests/unit/services/image_gen/test_ui_metadata_negative_prompt_notes.py -q`
- Docker: `./docker/build_prod_images.sh`
- Chrome E2E (MCP):
  - 打开 `http://localhost:8089/virtual-ip/1`，进入任意图片「图生图」弹窗
  - DevTools Network: `GET /api/v1/ai/models/available?model_type=image_to_image` (reqid=125, 200) 响应中包含 `metadata.ui.image_gen.*.notes` 的 negative_prompt 提示

## Next Steps

- 将更多 provider/model 的参数差异（如 cfg_scale 映射、reference_images 支持）统一纳入 UI notes 与输入控件动态渲染。

## Linked Commits

- (pending)
