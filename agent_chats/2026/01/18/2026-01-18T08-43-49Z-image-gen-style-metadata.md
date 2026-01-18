---
id: 2026-01-18T08-43-49Z-image-gen-style-metadata
date: "2026-01-18T08:43:49Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, frontend, image-gen, provider-aware]
related_paths:
  - ai-pic-backend/app/services/image_gen/ui_metadata.py
  - ai-pic-backend/tests/unit/services/image_gen/test_ui_metadata_style_spec_support.py
  - ai-pic-frontend/src/utils/modelUi.ts
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationForm.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationStyleFields.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentVariantModal.tsx
  - ai-pic-frontend/src/components/shared/modals/ImageToImageModal.tsx
  - docs/image-gen-provider-matrix.md
  - tasks.md
summary: "Add provider-aware style preset/spec UI gating for image generation."
---

## User Prompt

全局检查文生图/图生图提示词规范与 provider 参数一致性；按 provider 优化并在切换模型时动态加载输入；原子化分布提交；检查并更新 `tasks.md`。

## Goals

- 让前端能按 provider+mode 判断 `style_preset_id` / `style_spec` 是否会生效，避免“选了但参数被忽略”。
- 在文生图表单与图生图弹窗中：不支持则隐藏并清空，支持则正常展示。
- Environment 域保持一致：policy 已禁用 style preset/spec，UI 不再误导展示。

## Changes

- Backend：`build_image_gen_ui_metadata()` 增加 `supports_style_preset_id` / `supports_style_spec`（text_to_image + image_to_image）。
- Backend tests：新增 `test_ui_metadata_style_spec_support.py` 覆盖可灵/Google 的支持差异。
- Frontend：`extractImageGenUi()` 解析新字段为 `supportsStylePreset` / `supportsStyleSpec`。
- Frontend：虚拟 IP 文生图表单在不支持时自动清空 `style_preset_id` / `style_spec`，并按能力隐藏输入。
- Frontend：`ImageToImageModal` 按能力隐藏/不提交 `style_preset_id` / `style_spec`；环境图生图弹窗显式禁用“风格预设”。
- Docs/Tasks：更新 `docs/image-gen-provider-matrix.md` 与 `tasks.md` 记录此能力矩阵变化。

## Validation

- Backend：`pytest -q tests/unit/services/image_gen/test_ui_metadata_style_spec_support.py tests/unit/services/image_gen/test_ui_metadata_reference_images.py tests/unit/services/image_gen/test_ui_metadata_negative_prompt_notes.py`
- Frontend：`cd ai-pic-frontend && npm run lint`（仅 warnings）
- Chrome E2E（http://localhost:8089）：
  - 环境详情页打开“图生图”弹窗：确认不再出现“风格预设”输入（避免误导）。
  - 虚拟 IP 详情页图片管理区点击“AI 生成图片”：
    - provider=可灵：出现“风格预设”与“高级风格（只传选中的维度）”
    - provider=Google：上述两项消失
- Docker：`./docker/build_prod_images.sh`

## Next Steps

- 评估是否把 Environment 的 `style` 语义注入 `environment_image.txt`（目前更多是参数层面的 style，而非 prompt 语义）。
- 继续补齐 provider×domain 的提示词语义检查与 UI 动态表单约束（例如 img2img 多参考图上限、strength 适配等）。

## Linked Commits

- (TBD)
