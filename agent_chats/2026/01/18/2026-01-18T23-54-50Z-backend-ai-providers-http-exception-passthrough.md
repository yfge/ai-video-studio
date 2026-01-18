---
id: 2026-01-18T23-54-50Z-backend-ai-providers-http-exception-passthrough
date: 2026-01-18T23:54:50Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, api, error-handling, video]
related_paths:
  - ai-pic-backend/app/api/v1/ai_providers.py
  - ai-pic-backend/tests/unit/test_ai_providers_http_exception_passthrough.py
summary: "Preserve HTTP 400 errors for generate text/image/video/speech endpoints instead of wrapping as 500."
---

## User Prompt

全流程测试（DeepSeek 生文、Google 生图/生视频）；发现 `/api/v1/ai/generate/video` 在 provider 返回 400 时会被包成 500，导致前端错误信息不可用；要求原子化提交。

## Goals

- 保证 `/api/v1/ai/generate/*` 在抛出 `HTTPException` 时保留原始 status code 与 detail，便于前端与调试定位。

## Changes

- 后端：为 `generate_text` / `generate_image` / `generate_video` / `generate_speech` 增加 `except HTTPException: raise`，避免 400 被统一包装成 500。
- 测试：新增单测覆盖校验失败与 provider 错误时的 HTTP 400 透传。

## Validation

- 后端单测：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（794 passed）
- 生产镜像构建：`./docker/build_prod_images.sh`（通过）
- Chrome E2E（登录 `geyunfei`，在 Episode workspace 页面控制台执行 fetch）：
  - `POST /api/v1/ai/generate/video`（`image_url + google:veo-3.1-generate-preview`）返回 `400`，body `{"detail":"所有视频生成提供商都失败了"}`（不再被包装为 500）
  - `POST /api/v1/ai/generate/video`（空 payload）返回 `400`，body `{"detail":"必须提供prompt或image_url"}`

## Next Steps

- 继续排查 Veo image-to-video 400 的具体参数约束（可能是 image_url 可访问性/尺寸/格式/时长等限制），并在 UI/文档中给出提示。

## Linked Commits

- (this commit)

