---
id: 2026-07-24T22-16-00Z-story-novel-semantic-movement-filter
date: "2026-07-24T22:16:00Z"
participants: [user, codex]
models: [gpt-5.6-sol]
tags: [backend, story-novel, movement, semantics]
related_paths:
  - ai-pic-backend/app/services/story/story_novel_location_rules.py
summary: Filter semantic movement claims while preserving hard location gates.
---

## User Prompt

继续通过真实系统 API + MySQL 完成 48 章长篇；任何质量门禁失败时停止付费，
修复正确链路而不绕过 Canon、状态或 future gate。

## Goals

- 修复 Task 6642 语义审计把已完成的跨章移动再次作为 missing effect。
- 保留真正可执行的缺失移动，并继续由确定性计划 validator fail closed。

## Changes

- 语义审计结果先按已验证前缀和当前批次的确定性状态重放。
- 同章已有相同 subject/from/to，或主体已经位于建议目标地点时，
  将审计建议识别为非 missing 并剔除。
- 起点仍连续的真实缺失移动继续进入计划，并接受原有 validator。
- 纯移动筛选拆到独立小模块，避免继续扩大语义审计热点文件。

## Validation

- Task 6642 fail closed，0 章。
- Invocation 1381 重复建议第 22 章 `loc-survey-ship -> loc-sunkbell`，
  但角色已在第 21 章抵达 `loc-sunkbell`。
- `pytest tests/unit/test_story_novel_plan_semantic_audit.py
tests/unit/test_story_novel_plan_semantic_audit_movements.py -q --no-cov`：
  12 passed。
- `pytest tests/unit/test_story_novel_*.py -q --no-cov`：
  408 passed，1 skipped。
- 精确 isort/black、repo docs/contracts diff、`git diff --check`：passed。
- 主审计文件 223 行，移动筛选 37 行，均低于 repo contracts 上限。
- 未重跑 `pre-commit --all-files`：上一提交已确认其既有全仓格式/ruff 基线失败
  且会自动改写 233 个非本任务文件；本次仅运行精确 hooks。
- `./docker/build_prod_images.sh`：passed（dirty build tag `3b1367af`）；
  backend manifest `fd06d2675c87634de38fb245efd973aed3354866a6c6d12e859e45ca59dd8e7a`，
  frontend manifest `16384696202d31b623cd4af8d819105400034c10653ccb2639468a37fce5140b`。

## Next Steps

- 精确提交、重启后，只 Resume 当前 Revision 一次。

## Linked Commits

- Pending
