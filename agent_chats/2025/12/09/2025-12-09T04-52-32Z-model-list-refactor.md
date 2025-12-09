---
id: 2025-12-09T04-52-32Z-model-list-refactor
date: 2025-12-09T04:52:32Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-models]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/providers/openai_provider.py
  - ai-pic-backend/app/services/providers/google_provider.py
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-backend/app/services/providers/deepseek_provider.py
summary: "Refactored provider model listing to call official APIs and prefer remote defaults"
---
## User Prompt
重构得到模型列表的逻辑，openai ,google,火山引擎 ,deepseek 都要在后端用api 调用官方的模型列表接口，模型不应该写死，现在做这个工作。

## Goals
- 改造 OpenAI、Google、火山引擎、DeepSeek 的模型列表获取方式为官方接口拉取。
- 让模型列表以远端为主，静态列表仅作为兜底，减少硬编码。
- 在服务管理层优先使用远端模型决定默认模型选择。

## Changes
- 为 OpenAI、Google、火山引擎、DeepSeek provider 添加远端模型拉取与类型/能力推断逻辑，避免依赖静态白名单。
- 在 AIServiceManager 中新增统一的 `_get_models_for_type`，默认模型选择与列表聚合都优先调用远端接口、静态配置兜底。
- 保留必要的静态模型作为失败回退，提升模型列表实时性。

## Validation
- `pytest`（全量）在 120s 超时前出现多处既有失败，未跑完。
- `pytest tests/test_ai_service.py`（通过）。
- 未执行 Chrome MCP 自测，因当前未启动前后端服务。

## Next Steps
- 启动完整后端/前端环境后补跑一次 Chrome MCP 端到端校验，并记录具体用例。
- 如果有外部接口权限，拉通全量 `pytest` 以确认环境依赖问题。

## Linked Commits
- (this commit)
