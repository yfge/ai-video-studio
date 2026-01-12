---
id: 2026-01-12T04-26-45Z-backend-img2img-error-details
date: 2026-01-12T04:26:45Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, ai, img2img, error-handling]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/tests/unit/test_ai_service_manager_image_to_image_error.py
summary: "Improve img2img failures to return provider-specific error details instead of a generic fallback."
---

## User Prompt

修复 “所有图生图提供商都失败了” 这个错误。

## Goals

- 当图生图失败时，返回可定位的 provider/model 错误信息（避免空错误/泛化错误）。
- 保持现有 fallback 行为不变，仅增强错误可观测性。

## Changes

- 强化 `AIServiceManager.image_to_image()` 的 `last_error` 采集：当 provider 返回空错误时也会落到可读占位符（`未知错误`），异常时确保 `last_error` 非空。
- 最终兜底错误从纯泛化文案改为包含“未捕获到具体错误信息”的提示，避免误导排查。
- 新增单测覆盖 provider/fallback 都返回空错误时，仍能得到带 provider 前缀的错误信息。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Chrome（Docker + Nginx dev，`http://localhost:8089`）：
  - 登录 `geyunfei` / `Gyf@845261`
  - DevTools Console 调用 `POST /api/v1/ai/generate/image-to-image`（`prefer_provider=keling`, `model=keling:not-a-real-model`）
  - 返回 `400` 且错误明细为 `model_name ... is invalid`，未出现“所有图生图提供商都失败了”的泛化提示

## Next Steps

- 将同类错误可观测性增强应用到 `generate_image()` 的兜底链路（文生图）与异步任务落库日志字段，减少“空错误”场景。

## Linked Commits

- fix(backend): improve img2img failure errors
