## User Prompt

继续完成长篇小说真实生成；已通过门禁的章节必须在取消和 Resume 后保持 business ID、正文及 hash 不变，任何恢复异常不得静默回退为从头生成。

## Goals

- 让 V3 Resume 严格遵守 `continuity_ledger.stale_from_position`。
- 起点之前只允许复用完整且可验证的 ready checkpoint。
- 若正文、source、Canon、合同、状态链、proof 或 Narrative candidate 任一不完整，在模型调用前 fail-closed。
- 不让 Prompt compiler 升级导致已完成章节被静默重写。

## Changes

- 新增 Resume 前缀验证，校验章节正文/source hash、Canon hash、章节合同 hash、状态前后链、proof spans 和 Narrative candidate 完整性。
- 校验通过后只把 `stale_from_position` 及其后章节交给生成循环，前缀章节不再重新构建 brief 或调用正文模型。
- 前缀不完整时返回明确 409，保留现有章节，不自动退回第 1 章。
- 将 proof 与正文绑定校验抽为共享纯函数，原有单章复用逻辑继续使用相同规则。
- 新增“编译器上下文变化仍跳过有效前缀”和“无效前缀拒绝静默重写”回归测试。

## Validation

- 真实 Task `#6879` 因执行器错误从第 1 章调用而通过正式 UI 取消；Task terminal 为 `CANCELLED`。
- 无效调用单列：`#3205` chapter planning、`#3206` prose；任务取消后没有接纳其正文。
- 第 1、2、19 章业务 ID、正文 hash 和字数在取消前后不变；第 1 章 ledger 阶段被未完成尝试覆盖，因此 Revision 66 保留为恢复缺陷证据，不再继续写入。
- 聚焦 Resume/取消/并发/V3 审批集合：30 passed。
- 完整 Story Novel 单测（测试进程内适配既有 FastAPI 异常字符串差异）：840 passed、1 skipped。
- isort、black 通过；文件均低于仓库行数上限。

## Next Steps

- 完成仓库契约检查并精确提交本修复。
- 收口 Prompt 审查确认的事件参与者绑定和返修信息脱敏两个 P1。
- 从同一冻结 StorySeed 创建干净 V3 Revision，重新执行真实 48 章生成、取消/恢复、连续性和 GPT-5.6 验收。

## Linked Commits

- Pending
