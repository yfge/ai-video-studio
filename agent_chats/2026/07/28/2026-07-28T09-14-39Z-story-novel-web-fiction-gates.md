## User Prompt

用户指出网文的核心是情节爽感与吸引力，要求确认当前判定是否过严、是否把生成链路
做成了严肃文学，并继续改造章前规划驱动的 V3 长篇生成链路。

## Goals

- 保留 future、Canon、状态、时间、知识、地点、里程碑与 hash 的确定性硬门禁。
- 将一般写实程度、劳动略快、戏剧化、节奏和文风降为非阻断编辑建议。
- 为每个 required event 冻结可执行语义，避免 brief 自行扩大事件规模或改变完成阶段。
- 提高慢速规划调用的可恢复性，并正确关闭取消后的 invocation 审计状态。

## Changes

- 新增 event execution contract，绑定 action phase、time scope、actors、effort、
  timeline 与 knowledge；V3 plan/brief 必须逐项保留该合同。
- 语义审计只把冻结合同间的直接矛盾标为 blocking；未明确规模保持 unspecified，
  通俗网文的写实度、节奏与戏剧化只记录 advisory。服务端按 issue code 归一严重度，
  不信任模型自报的 blocking/advisory；actor 仅允许本章可见 Canon 角色。
- 章前 brief 与正文 prompt 使用“压力/冲突—主角选择—行动—可见收益或代价—章末
  钩子”的商业网文节奏，并禁止把章节写成施工或审计报告。
- 全局与逐章规划均增加 180 秒总超时与一次传输重试；取消中的文本调用会把
  invocation 关闭为 cancelled，而不会遗留 processing 状态。
- 更新 V3 设计真源、Narrative Memory 设计、执行计划与任务板。

## Validation

- 精确执行合同、brief、timeout、invocation 与 V3 pipeline/approval/evidence：37 passed。
- 完整 `tests/unit/test_story_novel_*.py`：580 passed, 1 skipped。
- 精确 Python 路径 isort/black：通过。
- `check_repo_contracts.py --mode diff` 与 `git diff --check`：通过（文档更新前的代码
  checkpoint；交付前继续复跑）。

## Next Steps

- 完成独立只读代码审查、backend quick/full、前端与仓库级验证。
- 通过正式 API 从冻结 StorySeed 创建新的 V3 Revision；旧无 execution contract 的 V3
  Revision 只保留为失败证据，不静默迁移。
- 完成真实 48 章 cancel/Resume/hash 验证和 GPT-5.6 八批加全书审读后才能审批。

## Linked Commits

- Pending.
