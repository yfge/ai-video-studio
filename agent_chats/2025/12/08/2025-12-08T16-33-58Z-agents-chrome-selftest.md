---
id: 2025-12-08T16-33-58Z-agents-chrome-selftest
date: 2025-12-08T16:33:58Z
participants: [human, codex]
models: [gpt-4o]
tags: [process]
related_paths:
  - AGENTS.md
summary: "Emphasize mandatory Chrome self-test after each functional change in AGENTS guide."
---

## User Prompt

在 AGENTS.md 中强调：每一个功能完成以后，要用 Chrome 自测。

## Goals

- 更新 AGENTS.md，新增强制性的 Chrome 自测要求。
- 确保镜像文件（symlink）保持一致。

## Changes

- 在 `AGENTS.md` 的 Delivery Checklist 前增加“CRITICAL — Chrome self-test”提示：每个功能完成后需在真实 Chrome 浏览器做一次端到端验证（可用 DevTools/远程），并在 `agent_chats` 记录场景。

## Validation

- 文档更新为全局指令；CLAUDE.md / GEMINI.md 为 AGENTS.md 的符号链接，无需额外同步。

## Next Steps

- 遵循新要求：每个功能交付前在 Chrome 自测并记录到 agent_chats。

## Linked Commits

- (pending)
