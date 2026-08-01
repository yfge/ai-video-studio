---
id: 2026-07-24T19-40-25Z-story-novel-plan-semantic-audit
date: "2026-07-24T19:40:25Z"
participants: [user, codex, novel_code_review]
models: [gpt-5.6-sol, deepseek-v4-pro]
tags: [backend, story-novel, planning, canon-gate, semantic-audit, real-run]
related_paths:
  - ai-pic-backend/app/services/story/story_novel_plan_semantic_audit.py
  - ai-pic-backend/app/services/story/story_novel_planning_phases.py
  - ai-pic-backend/app/services/story/story_novel_planning_prompt.py
  - ai-pic-backend/app/services/story/story_novel_plan_repair.py
  - ai-pic-backend/tests/unit/test_story_novel_plan_semantic_audit.py
  - ai-pic-backend/tests/unit/test_story_novel_planning_batches.py
summary: Audit every planned event's typed effects before generating prose.
---

## User Prompt

继续完成 Canon 状态门禁与长篇小说质量闭环；AI 生成结构化章节时允许输入
章节数并选择规划模型，正文模型独立选择；同时以只读 review thread 审查小说生成
整体代码，由主任务决定是否采纳。

## Goals

- 保持用户选择的规划模型和正文模型在正式任务中分别冻结。
- 在正文生成前发现结构合法但语义不完整的章节合同。
- 不使用中文关键词正则推断计划效果，不放宽 runtime `illegal_knowledge` 门禁。
- 保持旧 v1/旧计划兼容，新 confirmed structured-outline v2 才声明语义审计保证。

## Changes

- 新增 8 章有界、`temperature=0` 的独立计划语义审计；审计输入只包含已验证
  前缀、当前批计划、Canon 实体/里程碑和冻结约束。
- 语义审计使用 16000 输出预算，保持长篇链路不回落到 8192 或更低的应用级上限。
- 审计响应必须逐项、同序、精确覆盖当前批全部 `required_event_ids`，额外、缺失
  或重复事件均 fail closed。
- 审计只返回计划遗漏的 `knowledge_grants`、`state_transitions`、
  `location_transitions` 和 `milestones_consumed`；系统定点合并后重放确定性计划
  validator，并在发生补丁时独立复审一次。
- 每章保存语义审计版本、事件 ID、章节合同 hash、审计响应 hash 和补丁计数；
  generation plan 保存 `plan_semantic_audit_version`。
- 非 Canon milestone 的新知识使用从 `source_event_id` 派生的稳定 fact ID，避免
  规划和独立审计为同一事实创建近义 ID。
- 真实 Task 6632 第 8 章证据表明：正文返修稿 3214 字，typed extraction 正确
  抽出王明/老拐各三项知识，但旧计划 `knowledge_grants=[]`，故 runtime 门禁正确
  fail closed；旧 Revision 不再直接 Resume。

## Validation

- `pytest -q --no-cov tests/unit/test_story_novel_plan_semantic_audit.py
tests/unit/test_story_novel_planning_batches.py` -> 9 passed。
- `pytest tests/unit/test_story_novel_*.py -q --no-cov`
  -> 383 passed, 1 skipped。
- 精确路径 `pre-commit` isort、black -> passed。
- `python scripts/check_repo_contracts.py --mode diff ...` -> passed。
- `python scripts/check_repo_docs.py` -> passed。
- `git diff --check` -> passed。
- 正式 Task 6633 首次运行的语义审计 invocation `#1347` 以 8000 预算触顶，
  `finish_reason=length`，正文前 fail-closed、0 章；据此把审计预算修正为 16000，
  并增加请求预算回归。Task 6633 的 17974 input / 26225 output tokens 单列为失败
  规划证据，不计入后续成功长篇正文指标。
- 一次从仓库根目录执行 backend 相对测试路径仅产生 file-not-found、0 tests；
  已在 `ai-pic-backend/` 正确目录复跑并通过，未触发 API、MySQL 写入或 provider。

## Next Steps

- 构建生产镜像并提交本切片。
- 通过正式产品 API 创建带语义审计证明的新 Revision，不复用 Task 6632 的无效
  计划；仅在计划审计和确定性重放通过后生成正文。
- 完成 48/48、连续性检查、GPT-5.6 分批和全书审读、审批与运行证据归档。

## Linked Commits

- Pending
