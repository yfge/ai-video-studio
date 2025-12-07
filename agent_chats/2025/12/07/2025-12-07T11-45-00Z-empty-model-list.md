---
id: 2025-12-07T11-45-00Z-empty-model-list
date: 2025-12-07T11:45:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-models]
related_paths:
  - ai-pic-backend/app/api/v1/ai_providers.py
  - ai-pic-backend/app/services/ai_service.py
summary: "Guard model-list endpoint when no providers are configured"
---

## User Prompt

- 调用 `/api/v1/ai/models/available?model_type=text` 返回为空。

## Goals

- 明确反馈无可用模型的原因，避免静默空列表。

## Changes

- `/api/v1/ai/models/available` 先检测已启用的 provider，缺失时返回 503 并提示需配置 OPENAI_API_KEY / VOLCENGINE_API_KEY 等。
- 若列出模型结果为空，同样返回 503 并提示检查提供商密钥或初始化错误。
- `get_ai_providers_status` 在 ai_manager 缺失时安全返回空字典，避免 AttributeError。

## Validation

- 未新增自动化测试（后端接口小改）；建议 curl 触发验证提示信息。

## Next Steps

- 补充健康检查端点或状态页，直观展示 provider 配置与可用模型。
- 若需要在无密钥情况下展示静态白名单，可再加“只读模式”开关。

## Linked Commits

- (pending)
