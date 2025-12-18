---
id: 2025-12-18T14-53-06Z-keling-duration-clamp
date: 2025-12-18T14:53:06Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, provider, keling]
related_paths:
  - ai-pic-backend/app/services/providers/keling_provider.py
summary: "Clamp keling image2video duration to allowed 5/10s to avoid 400 errors."
---

## User Prompt

- 可灵 image2video 返回 400；需要对照文档排查。

## Goals

- 避免向可灵发送不支持的时长（只允许 5 或 10 秒）。

## Changes

- 在 `keling_provider.generate_video` 中，将 duration 转 int 并限制为 5 或 10，取最接近值后再发起 image2video 请求；保持分辨率/画幅透传。

## Validation

- `pre-commit run --files ai-pic-backend/app/services/providers/keling_provider.py`（含 ruff/black/isort、backend quick gate）。
- 镜像 tag 93114fe 已构建；若需最新时长修复需再打包。

## Next Steps

- 部署后用 5/10 秒再次调用 keling，确认 400 消失；如仍失败，请收集响应 body（task_status_msg/code）。

## Linked Commits

- (pending)
