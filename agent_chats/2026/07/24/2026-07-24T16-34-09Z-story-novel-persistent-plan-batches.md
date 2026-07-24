## User Prompt

继续通过系统正式 API、真实 MySQL 和付费模型完成全新 48 章长篇，并验证
Canon、状态、未来剧情隔离、记忆、连续性及取消恢复链路。

## Goals

- 让每个已验证章节规划批次真实持久化，崩溃或失败后可从最后批次恢复。
- 只保留被冻结大纲明确支持的 Canon 物件地点里程碑结果。
- 不放宽最终章节计划 validator 或其他确定性质量门禁。

## Changes

- `reusable_plan_draft` 返回深拷贝，避免后续扩展原地修改 SQLAlchemy JSON。
- checkpoint 写入章节规划草稿时再次深拷贝，确保每批都会被识别为脏数据并提交。
- Canon 模型过滤版本升级到 v2；物件地点里程碑必须在其计划章节同时出现
  物件和目标地点，否则确定性剔除。
- 继续剔除在更早章节已同时出现物件和地点的重复里程碑结果。
- 新增真实 DB expire/reload 回归以及来源缺失、仅当前章来源和提前来源覆盖。

## Validation

- Task 6620 真实失败证据：
  - Revision `1fe57d4e72dd45f19281c3c524c2fbce` 为 48 章；
  - Task `1b8b4f61d62d4781a65dfcc9e5f0085c` 已 FAILED，正文 0 章；
  - MySQL 仅保存 32 章 `chapter_plan_draft`，暴露批次 JSON 原地变更漏写；
  - #1279/#1280 的四个第 48 章物件归档地点结果没有冻结大纲来源。
- focused planning/resume tests：19 passed。
- `pytest -q --no-cov tests/unit/test_story_novel_*.py`：
  369 passed, 1 skipped。
- 四个精确路径的 isort、black、repo contracts、repo docs 与
  `git diff --check` 均通过。

## Next Steps

- 重启 backend/worker 加载本提交。
- 只对 Revision `1fe57d4e72dd45f19281c3c524c2fbce` 发一次正式 Resume。
- 逐批核验 MySQL 规划草稿数 8、16、24、32、40、48，再进入正文。
- 至少两章 ready 后正式 cancel，保存 hash 快照，再正式 Resume 到 48/48。

## Linked Commits

- Pending
