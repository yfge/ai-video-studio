## User Prompt

接受将认知、能力、资源、活动/时间尺度作为可选成长曲线，用于全书规划和读者吸引力评审，而不作为逐章升级 KPI；继续完成真实长篇质量闭环。

## Goals

- 让连续性审读只把冻结 StorySeed 与编译 Canon 视为权威设定，避免旧人物档案与正文形成伪冲突。
- 明确 `state_before -> state_delta -> state_after` 是已确定性验证的状态链，避免把本章合法变化或窗口外历史变化误判为阻断。
- 保留具体 Canon 字段冲突、世界规则和正文硬门禁的 blocking 能力。

## Changes

- 相邻章节窗口改用紧凑冻结故事合同，不再重复输入旧 Virtual IP 人物背景。
- 窗口输入增加真源优先级、状态链语义、实际 state delta 与 state validation。
- 已通过确定性状态链的纯 state-before/expected-delta 审读问题降为编辑 warning；具体 Canon 字段冲突仍可 blocking。
- 增加旧人物档案隔离、章前状态语义和具体 Canon 冲突回归测试。

## Validation

- 聚焦连续性测试：18 passed。
- 完整 `tests/unit/test_story_novel_*.py`：100% 通过，1 skipped。
- black/isort（6 个精确文件）：通过。
- `check_repo_contracts.py --mode diff`（6 个精确文件）：通过。
- 真实产品连续性任务 #6889 已完成；全局 invocation #3507 为 478,819 字符、234,520 input tokens、3,809 output tokens、finish_reason=stop，证明上下文压缩修复有效。报告中 7 项确定性硬指标均为 0；本次代码继续处理其 3 个模型阻断误判来源。

## Next Steps

- 重启 backend/worker 加载本次修复，并从正式 UI 复跑一次连续性检查。
- 连续性通过后执行 GPT-5.6 八批审读和全书综合，生成 DOCX，最后再审批并提升 Canon。

## Linked Commits

- Pending.
