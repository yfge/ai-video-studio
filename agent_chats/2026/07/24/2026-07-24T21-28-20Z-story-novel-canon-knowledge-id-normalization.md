## User Prompt

继续完成真实系统 API + MySQL 的 48 章长篇生成；规划门禁失败时停止付费，
修复正确链路而不放宽 Canon validator。

## Goals

- 修复 Task 6637 第 19 章已消费里程碑、却因模型给 Canon knowledge fact ID
  增加自然语言前缀而 fail-closed 的模型解析问题。
- 保持原始计划 validator 对近义 ID 的严格拒绝和歧义时 fail-closed。

## Changes

- 模型计划解析可读取 Canon，在消费里程碑的同章内规范化 knowledge outcome。
- 仅当角色、当前章来源事件和逐字包含 Canon fact ID 的候选唯一时，替换为精确
  outcome value；不猜测来源事件，不处理歧义候选。
- 当模型只返回通用 fact ID 时，使用冻结 `thread_payoffs.evidence_key_event`
  与 required event 的一一对应关系编译 Canon knowledge outcome；只接受唯一绑定。
- 原始 `validate_generation_plan` 无变化。

## Validation

- Task 6637 fail closed，0 章；invocation #1366/#1367 均 `finish_reason=stop`。
- 精确错误：`里程碑结果未落地: mile-clock-drift-revealed
  char-wangming.knowledge contains '钟声频率偏移原因为地轴微动'`。
- #1367 模型实际给同一角色、同一 `ev-ch19-4` 的 fact ID：
  `知识-钟声频率偏移原因为地轴微动`。
- Task 6638 再次 fail closed，0 章；#1369 改用通用
  `fact-ev-ch19-4-1`，冻结 payoff 合同精确绑定同一 `ev-ch19-4`。
- focused：16 passed。
- `pytest tests/unit/test_story_novel_*.py -q --no-cov`：
  405 passed，1 skipped。
- 精确 isort/black、repo docs/contracts diff、`git diff --check`：passed。
- `./docker/build_prod_images.sh`：passed（dirty build tag `7aa6d94b`）；
  backend manifest `f4829d66b38c182e2520e6b6675a4348793e4a4db418635b5000419981ff6734`，
  frontend manifest `4eda35689e960b8ac4522de7d82d329826f33c688a16f2d66b17d6cc92044e62`。

## Next Steps

- 运行 focused/full Story Novel tests、格式、contracts 与生产镜像。
- 精确提交并重启 backend/worker 后，只 Resume 当前 Revision 一次。

## Linked Commits

- `7aa6d94b`
- Pending follow-up
