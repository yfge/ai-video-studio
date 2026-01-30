---
id: 2025-12-15T07-26-22Z-minimax-voice-service
date: 2025-12-15T07:26:22Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api, voice]
related_paths:
  - ai-pic-backend/app/services/minimax_client.py
  - ai-pic-backend/app/services/providers/minimax_provider.py
  - ai-pic-backend/app/services/voice_service.py
  - ai-pic-backend/app/api/v1/voice.py
  - ai-pic-backend/app/api/v1/api.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/providers/base.py
  - docs/api/minimax/
summary: "Add MiniMax shared client, voice service façade, and voice/music API endpoints with bilingual enums."
---

## User Prompt

实现 docs/api/minimax/ 下的所有 API，封装统一 client，初始化时拉取列表，增加 voice_service 顶层调用，并返回中英文枚举字典。

## Goals

- 统一 MiniMax 底层 HTTP client，供 provider 与语音能力复用。
- 覆盖文档中的语音合成、音色查询/删除、音色设计、音乐生成 API。
- 在上层暴露 voice_service 与 FastAPI 路由，返回中英文枚举字典并初始化预拉取列表。

## Changes

- 新增 `MinimaxClient` 与 `MinimaxAPIError`，统一构建 headers、loop-safe client 与 base_resp 校验。
- 重写 `MinimaxProvider` 语音模型列表、TTS 请求路径与错误处理；在 AIService 增加 MiniMax provider 配置，扩展 ProviderConfig 支持 group_id/region。
- 引入 `voice_service` 与 `MinimaxVoiceProvider`，初始化时预拉取音色列表，提供 TTS/voice design/voice delete/music generation，并输出中英文枚举与默认值。
- 新增 `/api/v1/voice/*` 路由（enums/voices/tts/design/delete/music），更新 v1 api 路由聚合；补充 MiniMax 文档目录。

## Validation

- `black app/services/minimax_client.py app/services/providers/minimax_provider.py app/services/voice_service.py app/api/v1/voice.py app/services/ai_service.py`
- `pytest`（本地环境大量失败：缺少测试夹具、数据库/服务未配置，HTTP 连接到 localhost:8000 失败，现有 e2e/迁移/模型测试依赖真实后端与外部服务，未在本次任务内修复）。
- 未运行 Chrome MCP 自测：本地未启动后端/前端服务，暂无法完成端到端浏览器验证。

## Next Steps

- 启动后端与前端服务后，用 ge/yunfei 测试账号在浏览器跑通 `/voice` 路由端到端，并在后续提交补充验证记录。
- 配置有效的 MiniMax API KEY/GROUP_ID 及可访问的数据库，重跑 `pytest` 与必要的 e2e 路径。
- 与前端对齐枚举/默认值展示及 TTS 参数需求，按需补充校验和示例。

## Linked Commits

- (this commit)
