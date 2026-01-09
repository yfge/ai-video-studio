---
id: 2026-01-09T10-18-16Z-image-gen-img2img-fallback-extra-images
date: "2026-01-09T10:18:16Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image, fix]
related_paths:
  - ai-pic-backend/app/services/image_gen/provider_params.py
  - ai-pic-backend/tests/unit/services/image_gen/test_normalize.py
summary: "Preserve reference images by keeping extra_images in img2img fallback filtering"
---

## User Prompt

继续 Phase 3（环境文生图/图生图/分镜图生图统一梳理落地）。在梳理环境 variants 的既有测试行为时，发现当未显式指定 model/provider 时仍需把参考图（extra_images）传递到 `ai_manager.image_to_image`。

## Goals

- 修复“provider 未解析时 img2img 参数过滤丢失 extra_images”的行为，避免环境 variants（以及其它 img2img 入口）在不指定 model 时丢失参考图。
- 增加单测覆盖该降级路径，作为后续接入环境链路的前置保障。

## Changes

- 更新 `ai-pic-backend/app/services/image_gen/provider_params.py`：
  - img2img fallback allowlist 增加 `extra_images`，确保 provider 不确定时仍能传递参考图列表（供 AIServiceManager 预读取/内网 URL 转 base64 使用）。
- 更新单测 `ai-pic-backend/tests/unit/services/image_gen/test_normalize.py`：
  - 新增用例覆盖 “provider/model 为空时 build_ai_manager_call 仍保留 extra_images”。

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/image_gen/test_normalize.py -q`

## Next Steps

- Phase 3：将环境文生图/图生图（sync + async + worker）接入归一化层，并补齐 Chrome E2E 验证记录。

## Linked Commits

- TBD
