---
id: 2025-12-18T13-20-00Z-keling-image2image
date: 2025-12-18T13:20:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, provider, image-to-image]
related_paths:
  - ai-pic-backend/app/services/providers/keling_provider.py
summary: "Enable keling provider for image_to_image tasks so env 图生图 finds available providers."
---

## User Prompt

- 环境图生图任务提示“没有可用的图生图提供商”，需要检查并修复。

## Goals

- 让可灵支持 image_to_image 能力，以便环境图生图任务能选到可用 provider。
- 重新构建生产镜像，准备部署。

## Changes

- `keling_provider.supported_model_types` 增加 `AIModelType.IMAGE_TO_IMAGE`，使可灵在图生图场景被选中（其模型 `kling-image-v2/v1` 已声明 `image_to_image` 能力）。

## Validation

- `pre-commit run --files ai-pic-backend/app/services/providers/keling_provider.py`（通过）。
- `bash docker/build_prod_images.sh`（通过，镜像 tag 2f0e220）。
- 未重跑全量 `pytest`（基线仍有 fixture/DB 失败），依赖 pre-commit backend quick gate。

## Next Steps

- 部署后端/worker 至镜像 `2f0e220`，重跑环境图生图任务（任务ID 322）应不再报“没有可用的图生图提供商”；完成后刷新环境详情页查看新增图片。

## Linked Commits

- (pending)
