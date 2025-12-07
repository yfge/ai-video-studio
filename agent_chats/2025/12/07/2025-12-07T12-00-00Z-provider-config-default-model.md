---
id: 2025-12-07T12-00-00Z-provider-config-default-model
date: 2025-12-07T12:00:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-models]
related_paths:
  - ai-pic-backend/app/services/providers/base.py
summary: "Fix provider config to carry default_model and silence model_id namespace warning"
---

## User Prompt

- /api/v1/ai/models/available 报错，日志显示 ProviderConfig 缺少 default_model，pydantic 对 model_id 提示 protected namespace。

## Goals

- 让 GoogleProvider 初始化不再因 default_model 缺失崩溃。
- 消除 model_id 的 protected namespace 警告，保持模型枚举正常。

## Changes

- ProviderConfig 新增 optional default_model/api_secret，开放 extra/namespace 以兼容传入字段，避免属性缺失。
- ModelInfo 设置 protected_namespaces 为空，去除 model_id 命名冲突警告。

## Validation

- 未跑自动化；需通过 curl /api/v1/ai/models/available 验证模型列表恢复（需配置对应 API key）。

## Next Steps

- 如仍为空，检查容器环境变量 OPENAI_API_KEY / VOLCENGINE_API_KEY / GOOGLE_API_KEY 等是否注入。

## Linked Commits

- (pending)
