---
id: 2025-10-18T07-14-55Z-atomic-commit-discipline
date: 2025-10-18T07:14:55Z
participants: [human, codex]
models: [gpt-5.1-codex]
tags: [docs, process]
related_paths:
  - AGENTS.md
summary: "Emphasised mandatory atomic commit discipline in agent guidance"
---

## User Prompt

每完成一个工作项后要及时提交，保证提交的原子性，把这个规则加到agents.md中并重点强调

## Goals

- 更新 AGENTS.md，突出说明工作项完成后必须立即提交。
- 确保相关镜像文件保持同步。
- 记录此次流程调整，便于后续审计。

## Changes

- 强调 agent ledger 规则第 7 条，明确原子提交是刚性要求。
- 在 Commit & Branch Policy 中新增粗体提示，禁止合并多个工作项到单次提交。

## Validation

- 未运行自动化校验（说明性文档更新）。

## Next Steps

- 继续监督后续工作流是否遵循原子提交要求。

## Linked Commits

- (pending)
