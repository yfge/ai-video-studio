---
id: 2025-12-11T11-09-11Z-backend-normalize-all-provider-keys
date: 2025-12-11T11:09:11Z
participants: [human, codex]
models: [gpt-5.1]
tags: [backend, ai-provider, config]
related_paths:
  - ai-pic-backend/app/core/config.py
summary: "Normalize all AI provider API keys to treat empty strings as unset, so disabled providers don't initialize or spam logs when env vars are left blank."
---

## User Prompt

用户反馈 GoogleProvider 未配置时已经降噪处理，希望其他 AI 提供商（OpenAI、火山、DeepSeek 等）在 `.env` 里留空 key 时也“类似处理”，不要被误判为已配置、初始化无效 provider 或制造多余日志。

## Goals

- 在配置层面对所有主要 AI provider 的 key 做统一规范化：空字符串视为未配置。
- 确保 AIService 初始化时只为真正有 key 的 provider 创建实例。
- 保持现有行为：缺失 key 时不抛异常、不影响其它 provider。

## Changes

- 更新 `ai-pic-backend/app/core/config.py`：
  - 在 `_normalize_optional_str` 基础上，将以下字段统一做 `strip()` 并将空字符串转为 `None`：
    - `GOOGLE_API_KEY`
    - `OPENAI_API_KEY`
    - `STABILITY_API_KEY`
    - `KELING_API_KEY`, `KELING_SECRET_KEY`
    - `JIMENG_API_KEY`, `JIMENG_SECRET_KEY`
    - `MINIMAX_API_KEY`, `MINIMAX_GROUP_ID`
    - `DEEPSEEK_API_KEY`
    - `VOLCENGINE_API_KEY`, `VOLCENGINE_SECRET_KEY`, `VOLCENGINE_REGION`
  - 这样 `.env` 中留白（如 `OPENAI_API_KEY=` 或带空格）时，这些字段都在启动时被视作 `None`，AIService 构建 providers 时会跳过对应 provider。

## Validation

- 运行 `python -m compileall app/core/config.py` 验证语法无误。
- 逻辑检查：
  - 当 `.env` 里某个 key 留空时，对应 `settings.*` 字段在应用启动后为 `None`，`AIService._get_ai_service_manager` 中的 `if settings.<PROVIDER>_API_KEY:` 判断将返回 False，不再创建该 provider。
  - 其他已配置 provider 行为不变，模型列表和调用逻辑保持原样。

## Next Steps

- 在生产 Docker `.env` 中安心保留空的占位行（例如复制模板后暂时不填），不会再误触发半配置状态的 provider。
- 如需启用特定 provider，只需填入有效 key 并重启后台服务。

## Linked Commits

- （待补充）`fix(backend): normalize all provider keys` 提交关联此更改。

