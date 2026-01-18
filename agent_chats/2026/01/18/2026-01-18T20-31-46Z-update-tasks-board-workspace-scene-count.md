---
id: 2026-01-18T20-31-46Z-update-tasks-board-workspace-scene-count
date: 2026-01-18T20:31:46Z
participants: [human, codex]
models: [gpt-5.2]
tags: [chore, tasks]
related_paths:
  - tasks.md
summary: "同步 tasks.md：记录 Episode workspace 概览场景数修复已完成"
---

## User Prompt
检查并更新 `tasks.md`。

## Goals
- 让任务板及时反映已完成的修复，便于后续排期与回归验证。

## Changes
- 在「Fix: 剧本生成稳定性（避免 mock 回退）」章节补充并勾选：Episode workspace 概览“场景数”展示所选剧本的实际场景数（避免误读）。

## Validation
- 文档变更：无需运行 `pytest` / `npm run lint`；本次提交不影响运行时逻辑。

## Next Steps
- 继续维护任务板：把后续 provider/domain 的提示词与表单动态优化拆分为可验证的小任务，按原子提交节奏推进。

## Linked Commits
- chore(tasks): update tasks board for workspace scene count fix

