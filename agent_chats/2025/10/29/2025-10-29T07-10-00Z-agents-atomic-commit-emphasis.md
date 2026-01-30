---
id: 2025-10-29T07-10-00Z-agents-atomic-commit-emphasis
date: 2025-10-29T07:10:00Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [process, docs]
related_paths:
  - AGENTS.md
summary: "Strengthened AGENTS.md with an explicit atomic commit discipline callout per user request"
---

## User Prompt

及时提交现有更改，并将“时刻保持最小的原子化提交”的要求重点加入 AGENTS.md。

## Goals

- Make the atomic commit expectation impossible to miss for all collaborating agents.
- Capture staging + ledger pairing instructions alongside clean-working-tree requirements.

## Changes

- Introduced an “Atomic Commit Discipline (Critical)” section in `AGENTS.md` highlighting immediate commits, matching ledger entries, and clean worktree expectations.

## Validation

- Documentation-only update; verified `CLAUDE.md` / `GEMINI.md` remain symlinked to `AGENTS.md`.

## Next Steps

- Continue enforcing the updated guidance via pre-commit hooks and code reviews.

## Linked Commits

N/A
