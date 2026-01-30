---
id: 2026-01-15T09-12-42Z-image-gen-ui-metadata-reference-images
date: 2026-01-15T09:12:42Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen]
related_paths:
  - ai-pic-backend/app/services/image_gen/ui_metadata.py
  - ai-pic-backend/tests/unit/services/image_gen/test_ui_metadata_reference_images.py
summary: "Align txt2img supports_reference_images UI metadata with actual provider params"
---

## User Prompt

全局检查文生图/图生图提示词规范；模板语义是否正确、是否与所有 provider 参数一致；并按 provider 动态加载输入，原子化分布提交。

## Goals

- 修正文生图「参考图」能力的 UI 元数据，避免前端在不支持的 provider/model 上展示误导性输入。
- 为后续按 provider 动态加载 reference_images 输入打基础。

## Changes

- 更新 `build_image_gen_ui_metadata()`：`text_to_image.supports_reference_images` 仅基于实际 `supported_ai_manager_keys()` 返回的参数键（`reference_images/extra_images`），不再因 `caps` 包含 `image_to_image` 而误判。
- 新增单测覆盖：OpenAI（即使存在 img2img capability）仍不暴露 txt2img reference_images；Google 维持支持。

## Validation

- `pytest -q tests/unit/services/image_gen/test_ui_metadata_reference_images.py tests/unit/services/image_gen/test_ui_metadata_negative_prompt_notes.py`
- `./docker/build_prod_images.sh`
- Chrome (MCP): 打开 `http://localhost:8089/environments/aab17f172446462a97e738772337d272`，检查 `GET /api/v1/ai/models/available?model_type=text_to_image` (reqid=861) 返回的 `openai:dall-e-2` / `openai:dall-e-3` 均为 `image_gen.text_to_image.supports_reference_images=false`，Google 为 `true`。

## Next Steps

- 后端：环境文生图 `generate-async` 入口补齐 `reference_images` + `backend_base` 透传与归一化。
- 前端：在环境文生图表单中按 `extractImageGenUi(model, "text_to_image").supportsExtraImages` 动态展示参考图选择器并提交 `reference_images`。

## Linked Commits

- (pending)
