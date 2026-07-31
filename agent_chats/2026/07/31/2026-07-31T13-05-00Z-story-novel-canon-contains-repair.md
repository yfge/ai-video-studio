## User Prompt

用户要求继续真实种田文长篇生成，同时保持成长为全书软曲线、逐章硬合同只验证大纲授权的真实升级。

## Goals

- 修复真实 v33 Canon 两次都因标量字段误用 `contains` 而失败的问题。
- 保留现有 Canon validator，不把错误状态放宽通过。

## Changes

- Canon 提示词明确数组、关系映射和标量字段各自允许的 outcome operator。
- Canon 修复上下文确定性回放 milestone outcomes，标出 `contains` 的标量目标 milestone。
- 修复模型必须把该 outcome 改成有来源的 `eq` 状态或删除，不能把标量初态改成数组。
- 增加 prompt 与 repair-context 回归测试。

## Validation

- Exact Canon repair and prompt tests: 6 passed.
- Canon state, milestone outcomes, organization knowledge, and repair context: 23 passed.
- Exact-path isort and black hooks passed.
- Repository contracts diff and exact-path `git diff --check` passed.

## Next Steps

- 验证后重启 backend/worker，并只重试 v33 的规划与正文任务。
- Canon 通过后重新执行两章 cancel/resume hash 验收。

## Linked Commits

- Pending.
