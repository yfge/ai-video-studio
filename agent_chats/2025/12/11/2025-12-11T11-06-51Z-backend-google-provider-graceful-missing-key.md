---
id: 2025-12-11T11-06-51Z-backend-google-provider-graceful-missing-key
date: 2025-12-11T11:06:51Z
participants: [human, codex]
models: [gpt-5.1]
tags: [backend, ai-provider, models]
related_paths:
  - ai-pic-backend/app/core/config.py
  - ai-pic-backend/app/services/providers/google_provider.py
summary: "Make GoogleProvider quiet when GOOGLE_API_KEY is effectively unset and downgrade noisy list-models exceptions while still falling back to static models."
---

## User Prompt

在生产环境没有配置（或已经删除）`GOOGLE_API_KEY` 后，日志里仍然反复出现 `GoogleProvider list models exception:`，希望在未正确配置 Google 时不要频繁报警，模型列表接口仍然正常工作并回退到静态模型列表。

## Goals

- 当 `.env` 中的 `GOOGLE_API_KEY` 为空字符串或只含空白时，将其视为“未配置”，完全跳过 Google provider 的远端模型拉取。
- 减少 Google 模型列表拉取失败时的日志噪音，但仍保留回退到静态模型列表的行为。
- 不影响已有的 Google 文生图 / 图生图错误消息和行为。

## Changes

- 在 `app/core/config.py` 中为可选密钥添加简单规范化函数：
  - 新增 `_normalize_optional_str`，对可选字符串进行 `strip()`，并将空字符串标准化为 `None`。
  - 对 `settings.GOOGLE_API_KEY` 应用该函数，使 `.env` 中 `GOOGLE_API_KEY=` 或仅有空格时不会被当作“已配置”，从而不会在 `AIService` 初始化时注册 Google provider。
- 在 `app/services/providers/google_provider.py` 中调整远端模型拉取的日志级别：
  - 保留 HTTP 状态码 >= 400 时的日志，但将级别从 `warning` 调整为 `info`，注明“list models failed”并回退到静态列表。
  - 将 `GoogleProvider list models exception` 的日志级别降为 `debug`，避免网络波动或配置问题时在生产日志中反复刷屏。
  - 依旧在所有异常情况下返回预置的 `fallback` 模型列表，不影响 `/api/v1/ai/models/available` 功能。

## Validation

- 运行 `python -m compileall app` 以快速语法检查，确认 `config.py` 与 `google_provider.py` 通过编译。
- 逻辑验证：
  - 当 `.env` 中完全不设置 `GOOGLE_API_KEY` 或为 `GOOGLE_API_KEY=` 时，`settings.GOOGLE_API_KEY` 在启动后被标准化为 `None`，`AIService` 初始化时不会注册 `google` provider，也就不会发起远端模型列表请求。
  - 如果后续显式配置了有效的 `GOOGLE_API_KEY`，Google provider 仍会正常注册并尝试拉取远端模型；失败时仅记录一条 `info` 或 `debug` 日志，并回退到静态模型列表。

## Next Steps

- 在当前 Docker 环境中确认 `.env` 中没有残留形如 `GOOGLE_API_KEY=` 的空配置，或在需要时填入真实可用的 key。
- 通过 `/api/v1/ai/models/available` 观察模型列表是否仍然包含其他 provider 的模型，并确认日志中不再大量出现 Google list models 的异常警告。

## Linked Commits

- （待补充）`fix(backend): normalize google api key and quiet model list errors` 提交记录此更改。
