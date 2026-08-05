---
id: 2026-07-31T13-47-22Z-story-novel-priority-evidence
date: "2026-07-31T13:47:22Z"
participants: [user, codex]
models: [gpt-5.6-sol]
tags: [backend, story-novel, evidence, real-run]
related_paths:
  - ai-pic-backend/app/services/story/story_novel_priority_evidence.py
summary: Preserve source-bound priority evidence during long-form generation.
---

## User Prompt

实现章前规划驱动的长篇质量链路，并在真实 48 章生成中保证世界事件、人物记忆只供规划使用；模型实际看过的连续性证据不得在解析期被错误判为越界。

## Goals

- 修复 Task 6911 第 5 章的 continuity watchpoint 假阳性。
- 保持未知/未来 evidence ID 严格 fail-closed。
- 让同一证据集合在规划解析、checkpoint 和 Resume 中保持 hash 可复现。

## Changes

- 从章前 brief 提取被 watchpoint 实际引用的 evidence ID。
- 解析 typed chapter contract 后，优先把这些 Event/Memory 放入 32K 规划上下文；可选摘要、尾部和未引用证据让位。
- Resume 重建上下文时沿用 checkpoint brief 的 evidence 优先级。
- 如果已授权 evidence 本身超过预算，返回明确错误；未在当前修订版有效候选中的 ID 仍由原 validator 拒绝。
- 增加 package 重建、优先级裁剪和旧解析测试桩兼容回归。

## Validation

- `pytest -q tests/unit/test_story_novel_continuity_watchpoints.py tests/unit/test_story_novel_chapter_package_context.py tests/unit/test_story_novel_chapter_package_execution.py tests/unit/test_story_novel_chapter_package_stale_refs.py --no-cov` -> 14 passed.
- `pytest -q tests/unit/test_story_novel_*.py --no-cov` -> 881 passed, 1 skipped.
- `pre-commit run isort --files <8 exact paths>` -> passed after one mechanical import-order fix.
- `pre-commit run black --files <8 exact paths>` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <8 exact paths>` -> ok.
- `pre-commit run --all-files` 未执行：共享 worktree 仍有约 300 个无关 dirty/WIP 文件，改用本提交 8 条精确源码/测试路径的 isort、black、contracts，避免吸收或机械改写他人切片。
- Real MySQL evidence: Task 6911 stopped before chapter 5 prose; chapters 1-4 remain ready. Invocation 3841/3842 prompts contained legitimate memory IDs `a0365065...` and `1ff8af68...`, while the parser's recomputed context had budget-truncated them.

## Next Steps

- Restart backend and worker with this commit loaded.
- Formally Resume revision `320febd173bb4cb0a54025647f6140ea` once and verify chapters 1-4 hashes stay unchanged.
- Continue to 48/48, run continuity review, GPT-5.6 batch/global review, Word export and approval only if all gates pass.

## Linked Commits

- Pending.
