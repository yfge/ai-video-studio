---
id: 2026-01-30T02-08-11Z-repo-trailing-whitespace
date: 2026-01-30T02:08:11Z
participants: [human, codex]
models: [gpt-5]
tags: [chore, repo, formatting]
related_paths:
  - AGENTS.md
  - .gitignore
summary: "Apply trailing whitespace cleanup across repository via pre-commit hook"
---

## User Prompt

提交已经有的更改，清理工作区；接受一次性的大范围空格清理提交。

## Goals

- 让 `pre-commit` 的 `trailing-whitespace` hook 在全仓库范围内干净通过。
- 将“机械式格式化变更”与后续功能修复拆成独立原子提交，降低 review 负担。

## Changes

- 运行 `pre-commit run --all-files` 时触发 `trailing-whitespace` 自动修复，对全仓库大量文件移除行尾空格（不改变语义）。
- 本次提交仅包含该机械式格式化变更，不包含功能逻辑改动。

## Validation

- `pre-commit run --all-files`（trailing whitespace 清理后通过；其余 hooks 通过）

## Next Steps

- 继续提交“对白音轨旁白化”修复（TTS 前拆分引号对白并映射到 Story 注册角色），并在 docker 环境复测端到端。

## Linked Commits

- (pending) chore(repo): trim trailing whitespace

