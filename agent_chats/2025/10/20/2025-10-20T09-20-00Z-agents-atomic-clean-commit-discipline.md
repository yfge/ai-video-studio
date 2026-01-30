---
id: 2025-10-20T09-20-00Z-agents-atomic-clean-commit-discipline
date: 2025-10-20T09:20:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [docs, process]
related_paths:
  - AGENTS.md
summary: "Emphasize minimal atomic commits, minimal diffs, and keeping the working tree clean."
---

## User Prompt

将“最小化原子提交、最小更改提交、保持工作区干净”的要求加入并强调到 AGENTS.md。

## Goals

- 在《Commit & Branch Policy》中显式强调：
  - 仅允许最小原子提交；
  - 限定最小改动范围；
  - 提交前保持工作区干净（无未暂存变更）。

## Changes

- 在 `AGENTS.md` 的“Commit & Branch Policy”章节新增 “CRITICAL — Minimal Atomic Commits & Clean Workspace” 小节；
- 在“Delivery Checklist for Agents”中补充“工作区干净”检查项。

## Validation

- 文档更新最小化、措辞清晰，与现有“Atomic commits are mandatory”保持一致并进一步强化。

## Next Steps

- 保持 CLAUDE.md、GEMINI.md 作为 `AGENTS.md` 镜像（当前为符号链接，已自动同步）。

## Linked Commits

- pending（本地此次改动将与本账本条目一同提交）
