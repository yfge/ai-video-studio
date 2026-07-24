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
- 原始 `validate_generation_plan` 无变化。

## Validation

- Task 6637 fail closed，0 章；invocation #1366/#1367 均 `finish_reason=stop`。
- 精确错误：`里程碑结果未落地: mile-clock-drift-revealed
  char-wangming.knowledge contains '钟声频率偏移原因为地轴微动'`。
- #1367 模型实际给同一角色、同一 `ev-ch19-4` 的 fact ID：
  `知识-钟声频率偏移原因为地轴微动`。
- focused：8 passed。
- `pytest tests/unit/test_story_novel_*.py -q --no-cov`：
  403 passed，1 skipped。
- 精确 isort/black、repo docs/contracts diff、`git diff --check`：passed。
- `./docker/build_prod_images.sh`：passed（dirty build tag `7a9e40a3`）；
  backend manifest `38b15db5b165dc389ea5dcae8444040227bbd2363dc10bf1412b24c0a2c2d20e`，
  frontend manifest `2df8f6471b433ac3e1dc2c109b5c34036119841596c6c7c2bca1534da1937550`。

## Next Steps

- 运行 focused/full Story Novel tests、格式、contracts 与生产镜像。
- 精确提交并重启 backend/worker 后，只 Resume 当前 Revision 一次。

## Linked Commits

- Pending
