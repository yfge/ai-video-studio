---
id: 2025-12-22T07-06-48Z-fix-presigned-image-download
date: 2025-12-22T07:06:48Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, image, bugfix]
related_paths:
  - ai-pic-backend/app/utils/url_utils.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/image/image_persistence.py
summary: "Normalized presigned image URLs to prevent double-encoding during download."
---

## User Prompt
- 处理环境文生图任务失败（OpenAI 下载 403，签名无效）的问题

## Goals
- 避免下载预签名 URL 时发生二次编码导致签名失效
- 确保环境文生图任务可持久化并在详情页显示

## Changes
- 新增 `normalize_presigned_url`，对 query 中不安全字符（如 `/`）进行编码并保留已编码片段
- 在 `ai_service._download_image` 与 `image_persistence.download_image` 中统一使用该规范化逻辑

## Validation
- MCP Chrome: 登录 `http://localhost:8089` → 环境详情 `aab17f...` 创建环境图生成任务 → 任务页显示“已完成” → 环境详情显示 1 张参考图
- 容器内 `httpx` + `normalize_presigned_url` 请求示例 OpenAI URL 返回 200
- `pytest` (120s 超时，执行到 ~25% 仍有大量失败)
- `./docker/build_prod_images.sh`

## Next Steps
- 如需提升覆盖率，可补充 URL 规范化的单元测试
- 继续排查现有 pytest 失败项（多为既有环境/依赖问题）

## Linked Commits
- pending
