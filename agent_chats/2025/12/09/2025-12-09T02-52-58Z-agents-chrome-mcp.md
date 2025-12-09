---
id: 2025-12-09T02-52-58Z-agents-chrome-mcp
date: 2025-12-09T02:52:58Z
participants: [human, codex]
models: [gpt-4o]
tags: [process]
related_paths:
  - AGENTS.md
summary: "Add explicit Chrome MCP self-test rule with test account creds and no cost concern."
---

## User Prompt
“测试用户geyunfei 密码 Gyf@845261  每一个功能要用 chrome 的 MCP 进行自测，不用考虑所谓的大模型调用花费，加到 Agents.md 并重点强调。”

## Goals
- 在 AGENTS.md 强调：每个功能必须用 Chrome（MCP/DevTools）自测，使用指定测试账号，忽略模型调用成本顾虑。

## Changes
- `AGENTS.md` Delivery Checklist 加粗提示：每个功能完成后用 Chrome via MCP 自测并记录；登录使用 test user `geyunfei` / `Gyf@845261`；模型成本无需考虑。

## Validation
- 文档更新，无代码执行或测试。

## Next Steps
- 遵守新流程：所有功能交付前以 Chrome MCP 自测并在 `agent_chats` 记录。

## Linked Commits
- (pending)
