---
id: 2026-01-18T15-00-57Z-image-gen-max-count-ui-metadata
date: "2026-01-18T15:00:57Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, ui]
related_paths:
  - ai-pic-backend/app/services/image_gen/ui_metadata.py
  - ai-pic-backend/tests/unit/services/test_model_ui_image_gen_metadata.py
  - tasks.md
summary: "为 image_gen UI 元数据补齐 provider-aware 的 max_count，避免前端展示无效的“生成张数”。"
---

## User Prompt

- 和所有 provider 的参数一致么？能否根据 provider 再进一步优化，并在选择不同 provider 时动态加载输入（原子化分布提交）。

## Goals

- 将“生成张数”能力显式暴露给前端：当 provider 不支持 batch 返回多图时，前端可将 count 上限限制为 1 并提示用户。

## Changes

- 后端 `image_gen` UI 元数据新增 `max_count`：
  - `text_to_image.max_count`：按 provider/model 判断（例如 Google/Jimeng=1、Volcengine/Keling=4、OpenAI DALL·E 3=1）。
  - `image_to_image.max_count`：按 provider 判断（例如 Google/Jimeng=1、Volcengine/Keling/OpenAI DALL·E 2=4）。
- 单测补齐 `max_count` 的 provider-aware 行为断言。
- `tasks.md` 勾选后端 `max_count` 进度项。

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/test_model_ui_image_gen_metadata.py tests/unit/services/image_gen/test_ui_metadata_negative_prompt_notes.py tests/unit/services/image_gen/test_ui_metadata_reference_images.py tests/unit/services/image_gen/test_ui_metadata_style_spec_support.py`
- Chrome（localhost:8089）：登录后在 Console 请求
  - `GET http://localhost:8000/api/v1/ai/models/available?model_type=image_to_image`
  - 确认 `metadata.ui.image_gen.image_to_image.max_count` 返回：Google=1、Volcengine=4、Keling=4、OpenAI(dall-e-2)=4。

## Next Steps

- 前端：文生图/图生图弹窗按 `max_count` 动态限制输入并提示（超限自动裁剪/回退）。
- 后端：normalize 阶段做 provider-aware count clamp，并写入 `audit_warnings`（避免“填了但静默无效”）。

## Linked Commits

- TBD

