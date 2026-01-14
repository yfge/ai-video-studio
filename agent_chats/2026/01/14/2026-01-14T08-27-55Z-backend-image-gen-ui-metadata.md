---
id: 2026-01-14T08-27-55Z-backend-image-gen-ui-metadata
date: 2026-01-14T08:27:55Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, providers]
related_paths:
  - ai-pic-backend/app/services/ai/model_ui.py
  - ai-pic-backend/app/services/image_gen/provider_params.py
  - ai-pic-backend/app/services/image_gen/ui_metadata.py
  - ai-pic-backend/tests/unit/services/test_model_ui_image_gen_metadata.py
summary: "Expose provider-aware image generation parameter capabilities in model UI metadata"
---

## User Prompt

全局检查文生图/图生图的提示词规范；模板语义是否正确；各 provider 参数是否一致；能否根据 provider 进一步优化；并按 provider 动态加载输入，原子化分布提交。

## Goals

- 统一后端对各 provider 文生图/图生图参数的“可用键”定义，避免前端展示/后端过滤不一致。
- 在模型列表 API 中暴露可渲染的能力描述（哪些参数支持/不支持），用于前端按 provider/model 动态展示输入与提示信息。

## Changes

- 重构并集中维护文生图/图生图的 provider 参数白名单（支持键），并提供 `supported_ai_manager_keys()` 供过滤与 UI 元信息复用。
- 新增 `build_image_gen_ui_metadata()`，输出 `metadata.ui.image_gen`（按 provider + mode 的支持项与备注），包含 Volcengine `cfg_scale`（guidance_scale）模型差异与 Keling 图生图 `negative_prompt` 限制提示。
- 在模型 UI 组装逻辑中注入上述 `image_gen` 元信息。
- 新增单元测试覆盖 OpenAI/Jimeng/Keling/Volcengine 的差异化能力输出。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`

## Next Steps

- 前端：补齐各域请求 payload/types 的 `generation_profile` 与高级参数透传（t2i/i2i）。
- 前端：基于 `metadata.ui.image_gen` 动态展示/隐藏输入，并展示 provider 备注说明。
- E2E：Chrome 实测至少一条文生图与一条图生图路径（不同 provider/model）。

## Linked Commits

- (pending) feat(backend): provider-aware image-gen ui metadata
