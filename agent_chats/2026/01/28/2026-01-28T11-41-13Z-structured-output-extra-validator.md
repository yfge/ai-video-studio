---
id: 2026-01-28T11-41-13Z-structured-output-extra-validator
date: "2026-01-28T11:41:13Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, structured-output, validation]
related_paths:
  - ai-pic-backend/app/services/ai/structured_output.py
  - ai-pic-backend/tests/unit/services/ai/test_structured_output.py
summary: "Allow structured-output repair to enforce extra domain constraints (e.g. episode_count) via an extra_validator hook."
---

## User Prompt

- 继续按 `tasks.md` 推进 Phase 1：剧集生成需要严格结构化输出 + repair，并保证原子化提交。

## Goals

- 为通用 structured output repair 工具增加“额外约束校验”能力（不局限于 Pydantic schema），用于 episode_count 等域规则。
- 补充单测覆盖额外校验触发 repair 的路径。

## Changes

- Backend: `generate_with_repair(...)` 新增 `extra_validator`（Pydantic 校验通过后再跑一次额外约束；不满足则作为 validation_errors 进入 repair loop）。
- Tests: 新增用例覆盖 `extra_validator` 触发 repair 并成功修复。

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/ai/test_structured_output.py -q`

## Next Steps

- 在 episode plan 生成处接入 `extra_validator`，实现 episodes 数量与 `episode_count` 严格一致，并把 raw/normalized/errors/repairs 写入 `agent_run`。

## Linked Commits

- (pending)
