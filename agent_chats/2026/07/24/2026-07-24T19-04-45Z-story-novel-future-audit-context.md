---
id: 2026-07-24T19-04-45Z-story-novel-future-audit-context
date: "2026-07-24T19:04:45Z"
participants: [user, codex]
models: [gpt-5.6-sol, deepseek-v4-pro]
tags: [backend, story-novel, prompt-isolation, canon-gate, real-run]
related_paths:
  - ai-pic-backend/app/services/story/story_novel_context_utils.py
  - ai-pic-backend/app/services/story/story_novel_ai_prompts.py
  - ai-pic-backend/app/services/story/story_novel_repair_safety.py
  - ai-pic-backend/tests/unit/test_story_novel_future_outline_isolation.py
  - ai-pic-backend/tests/unit/test_story_novel_chapter_contract.py
  - ai-pic-backend/tests/unit/test_story_novel_future_repair_policy.py
summary: Keep chapter movement inside the current contract without invalidating ready checkpoints.
---

## User Prompt

继续通过正式 API、真实 MySQL 和付费模型完成 48 章长篇小说，确保正文 Prompt
只获得当前章大纲，并验证 Canon、状态、未来剧情、记忆和连续性门禁。

## Goals

- 保持 future audit 与状态 validator 的严格语义，不删除或放宽门禁。
- 当当前章没有地点移动合同时，明确禁止正文提前出发、登船、起锚或抵达。
- 保持既有 ready 章节的 context hash 与正文 checkpoint 可恢复。
- 从真实 Ch6 fail-closed 断点继续验证 48 章链路。

## Changes

- 正文生成和单次正文返修 Prompt 明确将 `location_transitions` 作为本章全部允许
  移动；空清单要求保持当前地点。
- `unexplained_location` 的安全返修指令改为删除未规划移动，而不是提示模型补写
  移动过程。
- 增加当前章移动边界和安全返修回归。
- 真实 Task 6631 证明，改变历史 soft context 会使 Ch2 ready checkpoint 的
  `context_hash` 漂移并在 provider 前 fail-closed。已撤回该兼容性破坏：
  既有 state audit 仅带未来事件技术 ID/`not_present`，不含未来章节标题、事件描述、
  目标、地点移动或结果；未来完整目录仍只提供给独立 state audit。

## Validation

- 真实运行 Task 6630：
  - Ch5 从 `gate_failed` 正式 Resume 后通过，3021 个非空白字符；
  - 调用 #1326–#1329 完成正文、状态、证据修复和 Narrative Memory；
  - Ch1–Ch4 body hash 保持不变；
  - Ch6 正确 fail-closed，未将提前完成的 Ch7 移动写入状态链。
- 真实 Task 6631：provider 前因 Ch2 context hash 漂移失败，0 次新模型调用、
  Ch1–Ch6 正文 hash 全部未变；据此撤回会改变历史 context hash 的方案。
- `pytest tests/unit/test_story_novel_future_outline_isolation.py
  tests/unit/test_story_novel_chapter_contract.py
  tests/unit/test_story_novel_future_repair_policy.py -q --no-cov`
  -> 15 passed。
- `pytest tests/unit/test_story_novel_*.py -q --no-cov`
  -> 377 passed, 1 skipped。
- 精确文件 `pre-commit` isort、black -> passed。
- `python scripts/check_repo_docs.py` 与精确路径
  `python scripts/check_repo_contracts.py --mode diff ...` -> passed。
- `./docker/build_prod_images.sh` -> backend/frontend 双架构生产镜像构建并推送成功；
  dirty-tree 验证使用脚本当时解析的标签 `d8149b40`。

## Next Steps

- 完成仓库契约和生产镜像验证后提交本切片。
- 重启正式 backend/worker，仅对 Revision
  `1fe57d4e72dd45f19281c3c524c2fbce` 调用一次 Resume。
- 继续生成至 48/48，再做连续性检查、GPT-5.6 分批/全书审读和正式审批。

## Linked Commits

- Pending
