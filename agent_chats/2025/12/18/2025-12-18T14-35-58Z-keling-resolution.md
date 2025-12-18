---
id: 2025-12-18T14-35-58Z-keling-resolution
date: 2025-12-18T14:35:58Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, provider, keling]
related_paths:
  - ai-pic-backend/app/services/providers/keling_provider.py
summary: "Pass resolution/aspect_ratio to Keling image2video to avoid 400 errors."
---

## User Prompt

- “之前可灵是好用的”，现在 keling image2video 返回 400，任务失败。

## Goals

- 让可灵 image2video 请求包含分辨率/画幅参数，避免 400。

## Changes

- `keling_provider.generate_video` 解析 resolution/ratio（含 kwargs），填入 image2video 请求的 `resolution`/`aspect_ratio` 字段，保持尾帧、camera_control 等逻辑不变。

## Validation

- `pre-commit run --files ai-pic-backend/app/services/providers/keling_provider.py`
- `pytest`（全量尝试 120s 超时、部分用例在 12% 处未跑完；需在有资源的环境复跑）
- 未再跑 e2e；`./docker/build_prod_images.sh` 待本次改动完成后统一执行。

## Next Steps

- 在有网络的环境重跑全量 `pytest`；部署后实际调用 keling image2video 验证 400 是否消失。

## Linked Commits

- (pending)
