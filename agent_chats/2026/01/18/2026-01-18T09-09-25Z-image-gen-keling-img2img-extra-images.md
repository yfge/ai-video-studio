---
id: 2026-01-18T09-09-25Z-image-gen-keling-img2img-extra-images
date: "2026-01-18T09:09:25Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, provider-aware, docs]
related_paths:
  - ai-pic-backend/app/services/image_gen/provider_params.py
  - ai-pic-backend/tests/unit/services/image_gen/test_ui_metadata_style_spec_support.py
  - ai-pic-backend/tests/unit/services/storyboard/test_storyboard_image_generation.py
  - docs/image-gen-provider-matrix.md
  - tasks.md
summary: "Align Keling img2img capabilities by disabling extra_images and syncing UI metadata/docs/tests."
---

## User Prompt

全局检查文生图/图生图提示词规范与 provider 参数一致性；支持按 provider 做进一步优化，并原子化提交。

## Goals

- 修正可灵（Keling）图生图对多参考图的能力描述，避免 UI/文档误导。
- 保持后端白名单、UI 元数据、文档矩阵一致。

## Changes

- `ai-pic-backend/app/services/image_gen/provider_params.py`：移除可灵 img2img 的 `extra_images` 支持（仅保留 base image）。
- `ai-pic-backend/tests/unit/services/image_gen/test_ui_metadata_style_spec_support.py`：补充断言（可灵 img2img `supports_extra_images=false`；Google=true）。
- `ai-pic-backend/tests/unit/services/storyboard/test_storyboard_image_generation.py`：更新用例期望（可灵 img2img 不再透传 `extra_images`）。
- `docs/image-gen-provider-matrix.md`：修正可灵 img2img `extra_images` 为不支持，并补充备注。
- `tasks.md`：补一条已完成项，记录该修正。

## Validation

- Backend quick gate：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Docker build：`./docker/build_prod_images.sh`
- Chrome E2E：
  - 打开 `http://localhost:8089/environments/5da63b15b5a640b380ef22cc30dc192b`
  - 点击任意参考图的「图生图」打开弹窗
  - 选择 provider=Google：不出现“该模型不支持多参考图”提示
  - 选择 provider=可灵：出现“该模型不支持多参考图”提示

## Next Steps

- 在归一化层补齐 provider 维度的“参数降级/丢弃”审计（seed/steps/cfg/strength 等），避免被静默过滤导致不可复现。
- 继续审计各 domain 的图像提示词模板语义一致性（single frame / no text / no collage）。

## Linked Commits

- (pending)
