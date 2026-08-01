---
id: 2026-07-24T22-29-00Z-story-novel-semantic-existing-effects
date: "2026-07-24T22:29:00Z"
participants: [user, codex]
models: [gpt-5.6-sol]
tags: [backend, story-novel, state, semantics]
related_paths:
  - ai-pic-backend/app/services/story/story_novel_plan_semantic_effects.py
summary: Reconcile existing state effects with semantic chapter validation.
---

## User Prompt

继续通过真实系统 API + MySQL 完成 48 章长篇；任何质量门禁失败时停止付费，
修复正确链路而不绕过 Canon、状态或 future gate。

## Goals

- 修复 Task 6643 最终复核把已写入计划的 milestone 原样再次报告为 missing。
- 只剔除与当前计划完全相同的 typed effect，不隐藏不同内容的新冲突。

## Changes

- 语义审计结果按当前章节计划精确去重 knowledge grants、state transitions
  和 consumed milestones。
- 地点建议继续使用已有移动与确定性状态去重。
- 不同值、不同主体或不同来源的 effect 保持原样，继续触发复核门禁。
- 最终复核显式携带首轮 `verification_targets`，只验证首轮补丁已写入，
  禁止在第二遍发明首轮未报告的新候选 effect。

## Validation

- Task 6643 fail closed，0 章。
- Invocation 1384 唯一非空项是第 19 章已经存在的
  `mile-clock-drift-revealed`。
- Task 6644 / Invocation 1387 在最终复核中新造首轮未报告的
  `ev-ch17-1` knowledge grant，证明复核职责需要收窄。
- `pytest tests/unit/test_story_novel_plan_semantic_audit.py
tests/unit/test_story_novel_plan_semantic_audit_movements.py -q --no-cov`：
  13 passed。
- `pytest tests/unit/test_story_novel_*.py -q --no-cov`：409 passed，1 skipped。
- 精确 `isort`、`black`、repo docs、repo contracts diff 与
  `git diff --check` 均通过；三个 Python 文件分别为 224、117、245 行。
- `./docker/build_prod_images.sh` 通过：
  - backend manifest
    `sha256:92b12f0154f7b6d88d1079ae3f3999afd015df444409d776accfa0a2e5871232`
  - frontend manifest
    `sha256:dd9447d0b612f492ef347740432d1c82c36e42df6480a120f0c383507dd2b34e`
- `pytest tests/unit/test_story_novel_*.py -q --no-cov`：
  409 passed，1 skipped。
- 精确 isort/black、repo docs/contracts diff、`git diff --check`：passed。
- 所有相关源码与测试文件均低于 250 行。
- 未重跑 `pre-commit --all-files`：已确认其既有全仓格式/ruff 基线失败并会
  改写 233 个非本任务文件；本次仅运行精确 hooks。
- `./docker/build_prod_images.sh`：passed（dirty build tag `c93c02cc`）；
  backend manifest `1fb96c3d90625275a831e5969af16b2b2d62fc340e7557f2ffc6a311d5a09796`，
  frontend manifest `6e1defa3513ef352e7aa1120e4471391f8df25c452df3d730aa0508a503adaac`。

## Next Steps

- 精确提交、重启后，只 Resume 当前 Revision 一次。

## Linked Commits

- Pending
