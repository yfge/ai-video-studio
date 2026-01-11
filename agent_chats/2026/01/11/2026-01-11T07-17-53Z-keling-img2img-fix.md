---
id: 2026-01-11T07-17-53Z-keling-img2img-fix
date: "2026-01-11T07:17:53Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, keling, img2img, docs, bugfix]
related_paths:
  - ai-pic-backend/app/services/providers/keling_provider/image.py
  - ai-pic-backend/app/services/providers/keling_provider/models.py
  - ai-pic-backend/app/services/providers/keling_provider/provider.py
  - docs/api/keling/capability-map.md
summary: "Align Keling img2img model support and normalize result image URLs"
---

## User Prompt

- 修复“所有图生图提供商都失败了”这个错误。
- 重新验证可灵（已充值），并确认 `docs/api/keling/capability-map.md` 与实测能力是否一致。

## Goals

- 用真实请求确认可灵各模型对图生图的支持情况，避免 UI/默认模型误导。
- 修复图生图链路中导致任务失败的根因，保证虚拟 IP 图生图端到端可用。
- 同步更新能力文档，避免后续误用。

## Changes

- 调整可灵图像模型能力映射：新增 `kling-v2`（支持图生图），并移除 `kling-v2-1` 的 `image_to_image` 能力，避免图生图误选。
- 将可灵 `image_to_image()` 默认模型从 `kling-v2-1` 改为 `kling-v2`。
- 可灵图像请求参数对齐：图生图场景不发送 `negative_prompt`；兼容/修正 `image_reference`；并为 `kling-v1-5` 在缺省时补齐必需的 `image_reference`。
- 修复可灵轮询结果返回 `images: list[dict]` 导致落库阶段对 dict 调用 `.startswith()` 崩溃：在轮询提取阶段统一归一为 `list[str]`（URL）。
- 更新 `docs/api/keling/capability-map.md`：将 `kling-v2-1` 图生图标注为不支持，并补充实测说明。

## Validation

- 可灵 API 实测（docker 内请求 `POST /v1/images/generations`）：
  - `kling-v2-1` 携带 `image` 返回 `The V2.1 model currently does not support image-to-image`。
  - `kling-v2` / `kling-v1` 图生图可提交任务；`kling-v1-5` 图生图需 `image_reference`。
- 后端测试：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（727 passed）。
- Chrome 端到端：
  - 登录 `http://localhost:8089/login`（geyunfei）。
  - 进入虚拟 IP「老拐」图片页，发起图生图，选择「可灵 / 可灵图像生成 V2」，提交后在任务页看到任务 `560` 状态变为「已完成」。

## Next Steps

- 继续 Phase 2：将 “generation_profile/preset” 在各图像入口（虚拟 IP / 环境 / 分镜）统一选择与展示，并补齐缺失的 provider/model 默认参数。

## Linked Commits

- (pending)
