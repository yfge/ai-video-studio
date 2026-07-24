## User Prompt

继续通过正式系统链路生成并验收全新 48 章小说；正确门禁不能为了通过样本而
放宽，真实规划失败时应定位并最小修复后继续。

## Goals

- 保持冻结结构化大纲的事件数量、顺序和正文内容为权威。
- 接受模型仅把中文弯引号改成直引号的无语义排版差异。
- 合并后始终恢复冻结大纲的精确事件文本，使 event ID 和知识来源绑定稳定。

## Changes

- `story_novel_outline_merge` 比较 key events 时只归一四个中英文单双弯引号，
  其余文字、数量和顺序仍需完全一致。
- 通过检查后仍由冻结大纲覆盖模型事件文本；没有放宽章节计划 validator。
- 新增回归证明直引号模型输出可接受、持久化结果恢复中文弯引号，同时保留
  required event IDs。

## Validation

- Task 6619 真实失败证据：
  - #1276 首稿无可解析 JSON；
  - #1277 修复后仅把第 34 章 `‘暗潮’` 改成 `'暗潮'`；
  - 系统 fail-closed，32 个规划草稿保留、0 个正文。
- `pytest -q --no-cov tests/unit/test_story_novel_outline_merge.py`
  - 10 passed。
- `pytest -q --no-cov tests/unit/test_story_novel_*.py`
  - 367 passed, 1 skipped。
- 两个精确路径的 isort、black、repo contracts、repo docs 与
  `git diff --check` 均通过。

## Next Steps

- 重启 backend/worker 加载本提交。
- 只对 Revision `1fe57d4e72dd45f19281c3c524c2fbce` 发一次正式 Resume，
  复用 32 个已验证规划草稿，从第 33 章继续。
- 规划完成后进入正文，完成至少两章的正式 cancel/hash snapshot/resume。

## Linked Commits

- Pending
