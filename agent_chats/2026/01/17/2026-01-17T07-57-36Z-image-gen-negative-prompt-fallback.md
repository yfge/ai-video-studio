---
id: 2026-01-17T07-57-36Z-image-gen-negative-prompt-fallback
date: 2026-01-17T07:57:36Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, provider-aware]
related_paths:
  - ai-pic-backend/app/services/image_gen/normalize.py
  - ai-pic-backend/tests/unit/services/image_gen/test_normalize.py
summary: "Normalize negative_prompt/reference_images to avoid silent drops on unsupported providers."
---

## User Prompt

全局检查文生图/图生图提示词规范；确认模板语义与各 provider 参数一致，并可按 provider 优化；分布式原子提交。

## Goals

- 避免 `negative_prompt` / `reference_images` 在不支持的 provider 上“看起来可填但实际被丢弃”
- 统一归一化层的审计信息（warnings/dropped_fields），便于前端提示与任务排查

## Changes

- `ai-pic-backend/app/services/image_gen/normalize.py`: 当 provider 不支持 `negative_prompt` 时将其合并进 `prompt`（`Avoid: ...`）并记录审计 warning；当 provider 不支持参考图时显式丢弃并记录 warning/`dropped_fields`
- `ai-pic-backend/tests/unit/services/image_gen/test_normalize.py`: 增加单测覆盖 negative_prompt 合并与 reference_images 丢弃告警

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/image_gen/test_normalize.py -q`
- `./docker/build_prod_images.sh`

## Next Steps

- Storyboard 图像生成：按 provider 能力区分“参考图 conditioning（txt2img）”与“base image（img2img）”策略
- 前端：在 Storyboard 等入口按模型能力动态限制/展示参考图输入并展示审计信息

## Linked Commits

- (pending)
