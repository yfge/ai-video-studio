---
id: 2025-12-18T06-36-05Z-env-image-download
date: 2025-12-18T06:36:05Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, environments, oss]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
summary: "Normalize signed image URLs to avoid double-encoding and failing environment image persistence."
---

## User Prompt
环境图像持久化失败: OpenAI DALL·E 返回的 SAS URL 在下载时被双重编码，日志报 403 Server failed to authenticate the request。

## Goals
- 修复环境图像下载逻辑，避免对已编码的签名 URL 再次编码导致 OSS 持久化失败。

## Changes
- 在 `AIService._download_image` 处理 URL 时，若包含 `%25`（双重编码迹象）先 `unquote`，并开启 `follow_redirects`，防止签名 URL 再次编码导致 403。

## Validation
- 手工分析 Celery 日志确认下载 URL 被编码为 `%253A` 触发 403；未能重跑完整 pytest，因本机缺少 `PyJWT` 依赖导致采集阶段报错（同样的已知环境问题）。

## Next Steps
- 安装缺失依赖 `PyJWT` 后重跑 `pytest`；重新触发环境文生图任务验证 URL 正常持久化。

## Linked Commits
- (pending)
