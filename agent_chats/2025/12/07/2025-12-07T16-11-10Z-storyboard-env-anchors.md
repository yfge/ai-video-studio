---
id: 2025-12-07T16-11-10Z-storyboard-env-anchors
date: 2025-12-07T16:11:10Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, storyboard, environment, character]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Inject environment/character reference images into storyboard image generation prompts"
---

## User Prompt

1. 分镜图生成链路：把场景 environment 的参考图 + 镜头角色图注入生成调用，并补一条 E2E 测试。

## Goals

- When生成分镜图像，自动把场景绑定的环境参考图和镜头角色参考图写入 prompt，并记录到帧的 reference_images，保证生成锚点。

## Changes

- `scripts.py` `_process_storyboard_image_task` 现在预加载 scenes→environment reference_images、shots→character_ids、VirtualIP 默认图；构造分镜 prompt 时附带“参考图像”说明，并把环境/角色图填入 `reference_images`。
- Added URL normalizer to ensure本地 `/uploads/...` 可作为完整 http 链接传给模型。

## Validation

- `pytest tests/test_story_structure_endpoints.py -q`（pass）。
- 手工：场景 1 绑定 environment_id=2（有 2 张参考图），调用 `/scripts/4/storyboard/generate-images`（Seedream 4.5）任务成功下发；若生成失败会回退到已有逻辑但 prompt 已包含环境图 URL。Chrome 刷新 `/environments` 显示环境 2 已有 2 张参考图，用于锚点。

## Next Steps

- 让前端分镜页生成时自动刷新任务状态，并展示最终拼接的 prompt/参考图，方便核验锚点；补一条端到端回归（分镜页发起 → 任务成功 → 帧记录 reference_images）。

## Linked Commits

- pending
