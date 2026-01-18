---
id: 2026-01-18T14-42-01Z-image-gen-persist-spec-metadata
date: "2026-01-18T14:42:01Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen]
related_paths:
  - ai-pic-backend/app/services/story_structure/environment_image_generation.py
  - ai-pic-backend/app/services/ai/images_generation.py
  - ai-pic-backend/app/services/virtual_ip/image_variant_service.py
  - ai-pic-backend/app/services/storyboard/storyboard_image_generation.py
  - tasks.md
summary: "为环境/分镜/图生图落库补齐 width/height 等规格字段，方便审计与复现。"
---

## User Prompt

- 全局检查文生图/图生图的提示词规范与 provider 参数一致性；按 provider 进一步优化，并原子化分布提交。

## Goals

- 在生成记录里统一落盘规范化后的规格信息（`size/aspect_ratio/width/height`），避免 UI 选项“看似可选但无法追溯实际下发规格”。

## Changes

- 环境资产：在 `Environment.extra_metadata.last_*_generation` 中补齐 `size/aspect_ratio/width/height`。
- 虚拟 IP 图生图：在生成参数/元数据中补齐 `width/height`（随 normalize 结果写入）。
- 分镜图像生成：在返回的 `image_gen` 元数据中补齐 `width/height`。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Chrome（localhost:8089）：
  - 登录后进入 `http://localhost:8089/virtual-ip/233525e9045146d580a1d18ef4a28161#ip-images`，选择任一图片点击“图生图”，提交 1 次任务并等待完成。
  - 在 Console 中携带前端 `auth_token` 调用 `GET http://localhost:8000/api/v1/virtual-ips/1/images`，确认新生成图片的 `generation_params.width/height` 已落盘（示例：`1024x1024`）。

## Next Steps

- 虚拟 IP 文生图：补齐 `generation_params/metadata` 使用 normalize 后的 `size/aspect_ratio/width/height`（当前仍用请求原值）。
- 增补 `image_gen` UI 元数据 `max_count`，并让前端表单按 provider 动态限制生成张数。

## Linked Commits

- TBD

