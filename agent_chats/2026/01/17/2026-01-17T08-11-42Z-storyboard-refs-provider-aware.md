---
id: 2026-01-17T08-11-42Z-storyboard-refs-provider-aware
date: 2026-01-17T08:11:42Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, storyboard, image-gen, provider-aware]
related_paths:
  - ai-pic-backend/app/services/storyboard/storyboard_image_generation.py
  - ai-pic-backend/tests/unit/services/storyboard/test_storyboard_image_generation.py
summary: "Prefer txt2img reference_images for storyboard refs when provider supports it; keep img2img when strength is set."
---

## User Prompt

全局优化文生图/图生图提示词与参数一致性；按 provider 能力进一步优化（含 Storyboard 等域），并原子提交。

## Goals

- Storyboard 的“参考图”默认作为风格/身份锚点（conditioning），优先走支持 `reference_images` 的 txt2img 路径
- 当调用方显式提供 img2img 相关参数（如 `strength`）时，保持 img2img 行为不变

## Changes

- `ai-pic-backend/app/services/storyboard/storyboard_image_generation.py`: 根据 `model` 解析 provider；当 provider 支持 txt2img `reference_images` 且未提供 `strength` 时，用 `TEXT_TO_IMAGE + reference_images`；否则沿用 `IMAGE_TO_IMAGE (base + extra_images)`。
- `ai-pic-backend/tests/unit/services/storyboard/test_storyboard_image_generation.py`: 增加单测覆盖 Google refs → txt2img 与 `strength` 强制 img2img 的分支。

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/storyboard/test_storyboard_image_generation.py -q`
- Chrome（MCP）：
  - 登录 `http://localhost:8089/login`，进入 `http://localhost:8089/episodes/10/storyboard`
  - 点击任一帧的「选择参考图生成关键帧」→ 选择模型 `google:gemini-2.0-flash-exp` → 提交
  - Network：`POST /api/v1/scripts/17/storyboard/generate-images`（reqid=115）返回 `task_id=594`
- `./docker/build_prod_images.sh`

## Next Steps

- 前端：按模型能力限制参考图数量/模式（支持 conditioning vs 仅 base image），并把审计信息透出到 UI
- 文档：补齐 provider×domain 兼容矩阵（reference_images/negative_prompt/extra_images 等）

## Linked Commits

- (pending)
