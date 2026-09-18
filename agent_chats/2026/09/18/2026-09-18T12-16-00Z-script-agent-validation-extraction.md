## User Prompt

优化 ai-video-studio 的人类可维护性，先从 script_agent.py 开始，保持行为不变。

## Goals

- 第一轮只做职责提取，不修改 ScriptLangGraphAgent 的公开行为和生成流程。
- 将后生成验证从 LangGraph orchestration 中分离，降低单文件认知负担。
- 保留现有私有方法入口，降低现有测试和调用方回归风险。

## Changes

- 新增 app.services.script_validation.ScriptValidationSuite，集中角色、信息门、场景转场和剧本质量验证。
- ScriptLangGraphAgent 保留原私有验证方法作为薄委托层，调用新的 validation boundary。
- 未修改 LangGraph 节点、prompt、重试策略、duration 逻辑或返回字段。

## Validation

- 本次为 GitHub 远程只读分析后的结构性 extraction；当前会话无法在用户本地工作树执行 pytest/pre-commit。
- 变更刻意保持原验证实现主体不变，仅移动职责并保留兼容委托方法。

## Next Steps

- 在本地运行 script-agent 聚焦测试、Ruff/Black/isort 和 repository contract checker。
- 验证通过后继续提取 duration budgeting / repair policy，避免一次性大重构。

## Linked Commits

- This commit.
