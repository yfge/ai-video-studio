## User Prompt

用户确认将长篇成长拆为认知、能力、资源、活动/时间尺度四条可选软曲线；它们用于全书规划与最终吸引力审读，不成为逐章升级 KPI。用户同时要求人物与世界按剧情需要依次扩展，而不是从头到尾困在同一地点。

## Goals

- 保留已实现的软成长曲线、阶段规划与按章世界扩展边界。
- 修复 GPT-5.6 全书审读暴露的跨章资源、借用期限、债务、库存、耗时和因果前置遗漏。
- 保持原始 World Event/Character Memory 只进入章前规划，正文只读取派生约束。
- 让后置审计只拦截正文的实际矛盾，不要求逐字复述约束或每章升级。

## Changes

- 新增带来源绑定的 `continuity_watchpoints` 合同，限制为资源、义务、时间、因果和关系五类，引用既有 evidence ID 或 state subject ID。
- 章前 package 负责提炼 watchpoint；正文只读取约束摘要，proof audit 仅在正文明确矛盾时报告 unexpected claim；局部 block 返修继续携带相同约束。
- Prompt policy 升级到 v10，并保留 v1-v9 历史快照的结构可读性。
- 扩展确定性正文完整性检查，拒绝同一 block 内的长段逐字重复。
- 同步 Story Novel、Narrative Memory 设计真源、v3 exec plan 和 `tasks.md`。

## Validation

- Focused chapter planning/world expansion/watchpoint tests: 29 passed.
- Prompt/package/audit/repair focused tests: 33 passed.
- Prose integrity focused tests: 8 passed.
- Full Story Novel unit suite: 878 passed, 1 skipped. 首轮发现 v10 未进入
  planning invocation provenance 强校验；修复后精确 2 passed，整套复跑全绿。
- 13 条 Python 路径 black/isort check 通过；所有源码/测试文件均不超过仓库行数上限。
- `check_repo_docs.py`、精确路径 `check_repo_contracts.py --mode diff`、
  `git diff --check` 均通过。
- 真实运行证据将在部署当前提交后生成。

## Next Steps

- 跑完整 Story Novel 单测、格式、repo docs/contracts 与 diff check。
- 通过正式 UI/API 创建新 Revision，完成 48 章 cancel/resume 和 hash 证据。
- 用 GPT-5.6 分批及全书复核；未达阈值保持 draft，并导出带结论的 DOCX。

## Linked Commits

- This commit.
