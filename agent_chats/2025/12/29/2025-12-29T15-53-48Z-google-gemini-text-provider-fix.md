---
id: 2025-12-29T15-53-48Z-google-gemini-text-provider-fix
date: 2025-12-29T15:53:48Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, provider, google]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider/text.py
  - ai-pic-backend/tests/unit/test_google_provider_text.py
summary: "Hardened Google Gemini text generation parsing, fallback, and system prompt handling"
---

## User Prompt

Celery 日志在 Google 生成文本时出现：

- `Google stream failed ... 504 Gateway Time-out` 后 fallback
- `ERROR: google 错误: 'list' object has no attribute 'get'`
- 以及 `400 INVALID_ARGUMENT: Please use a valid role: user, model.`

用户要求检查 Google 调用并修复。

## Goals

- 修复 Google 文本生成在非预期 payload（list）下的崩溃
- 修复 stream 失败后 fallback 的 endpoint 选择
- 兼容 Gemini v1beta 的角色约束，避免 `system` role 报错

## Changes

- `ai-pic-backend/app/services/providers/google_provider/text.py`
  - 新增 `_iter_event_dicts()` / `_collect_text_and_usage()`，兼容 dict / list 形式的 SSE 事件与非流式响应，避免对 list 调用 `.get()` 导致崩溃。
  - 修复 endpoint：stream 使用 `:streamGenerateContent?alt=sse`，fallback 使用 `:generateContent`。
  - system prompt 不再注入 `role=system` 的 content，改为使用 `systemInstruction`（避免 400 “valid role: user, model”）。
- `ai-pic-backend/tests/unit/test_google_provider_text.py`
  - 增加覆盖：list payload 解析、stream 失败 fallback 到 `:generateContent`、systemInstruction 使用方式。

## Validation

- 单测：`cd ai-pic-backend && pytest -q tests/unit/test_google_provider_text.py`
- 生产镜像构建：`./docker/build_prod_images.sh`（脚本 tag 基于 git `HEAD`，dirty 工作区会导致 tag 与内容不一致；本次验证 tag 显示为 `4707ef0`）
- Chrome（MCP）回归：
  - 登录 `geyunfei`，访问 `http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=script&scriptId=51`
  - 点击“重新生成剧本”，选择 provider=google，model=Gemini 3 Pro Preview，确认后提示“剧本重新生成成功”
  - 观察 celery 日志：不再出现 `'list' object has no attribute 'get'` 与 `valid role: user, model` 相关错误

## Next Steps

- 进一步定位 `Google stream returned empty content`（SSE 可能存在多行/非 `data:` 前缀事件），决定是否增强 SSE 解析或直接默认非流式以提升稳定性。
- UI 模型列表里 `Gemini Pro Latest` 在当前 proxy 下返回 400（可能是模型名不被 proxy 支持），需要和后端可用模型清单做一致性收敛。

## Linked Commits

- (pending)
