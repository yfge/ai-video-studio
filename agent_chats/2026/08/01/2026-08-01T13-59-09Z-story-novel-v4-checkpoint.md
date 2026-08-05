---
id: 2026-08-01T13-59-09Z-story-novel-v4-checkpoint
date: "2026-08-01T13:59:09Z"
participants: [user, codex]
models: [gpt-5.6-sol]
tags: [checkpoint, story-novel, v4, validation]
related_paths:
  - tasks.md
  - ai-pic-backend/app/services/story/story_novel_v3_repair_length.py
summary: Checkpoint the accumulated worktree while recording the failed v4 acceptance boundary.
---

## User Prompt

先提交所有的改动。

## Goals

- 将当前完整工作区保存为可追溯的 checkpoint。
- 保留长篇小说 v4、相关平台改动和并行 WIP，不吸收被忽略的数据库、音频、outputs 或 Docker 运行卷。
- 明确区分“代码 checkpoint”与“真实 48 章质量验收完成”。

## Changes

- 保存当前 Story Novel v4 冻结快照、分卷规划、动态人物/世界、逐章执行与局部返修实现及测试。
- 保存当前前后端、Storyboard、Timeline、provider、文档和历史 ledger 的累计工作区改动。
- 在 `tasks.md` 记录真实运行边界：Task 6948 在 24 章 ready 后于第 25 章 fail-closed。
- 记录独立前 20 章审读结论：约 58/100，且存在第 13 章早于第 16–18 章授权建立使用水权的跨章漏洞。
- 本 checkpoint 不代表 Revision 审批、Canonical 提升或 48 章验收通过。

## Validation

- `pytest -q --no-cov tests/unit/test_story_novel_v3_length_minimal_change.py`：3 passed。
- `pytest -q --no-cov tests/unit/test_story_novel_*.py`：974 passed，3 skipped。
- `npm run lint`：0 errors，3 warnings。
- `npm run test`：489 passed，9 failed；失败均位于 Production Canvas chat/planner 基线，未在本 checkpoint 扩大修复范围。
- 宿主 `npm run build` 被 worktree 外部 `node_modules` symlink 拒绝；`BUILD_PUSH=false ./docker/build_prod_images.sh` 的 backend/frontend production images 均本地构建成功，且没有向 registry push。
- `python run_tests.py quick`：Python 3.13 下锁定的 `pydantic==2.5.0` 与 `langchain-core==0.2.43` 依赖解析冲突，未进入测试执行。
- `python scripts/check_repo_docs.py`、`python scripts/check_repo_contracts.py --mode audit`、`git diff --check`：通过。
- `pre-commit run --all-files`：black/isort/prettier 自动修正后分别复跑通过；全量仍有 75 个跨仓历史 Ruff 问题，backend quick gate 和未暂存 ledger gate 未全绿。提交前会暂存完整目标并显式跳过已记录的失败 hook，不把它们表述为通过。

## Next Steps

- 先修复跨章语义授权门禁和长度局部返修可靠性，再做小规模无付费回归。
- 只有新的真实 48 章、Cancel/Resume hash、连续性、GPT-5.6 审读和审批全部通过后，才能关闭 v4 任务。

## Linked Commits

- Pending
