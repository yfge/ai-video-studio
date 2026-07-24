---
id: 2026-07-24T20-21-44Z-story-novel-audit-location-boundary
date: "2026-07-24T20:21:44Z"
participants: [user, codex, novel_code_review]
models: [gpt-5.6-sol, deepseek-v4-pro]
tags: [backend, story-novel, planning, semantic-audit, canon-location, real-run]
related_paths:
  - ai-pic-backend/app/services/story/story_novel_plan_semantic_audit.py
  - ai-pic-backend/tests/unit/test_story_novel_plan_semantic_audit.py
summary: Bind plan semantic audit movements to Canon locations and batch-start state.
---

## User Prompt

继续通过系统正式 API、真实 MySQL 和付费模型生成全新 48 章小说，验证
Canon、状态链、未来剧情隔离、事实/记忆和连续性门禁，并完成取消/恢复、
GPT-5.6 审读、审批及证据交付。

## Goals

- 只修复真实计划语义审计暴露的地点合同缺口，不放宽确定性 validator。
- 禁止独立审计自行创建 Canon 之外的子地点或方向地点。
- 让审计获得当前批次开始前的真实状态，减少合法 ID 之间的错误猜测。
- 保持语义审计 16000 输出预算、逐事件完整覆盖和二次独立复审。

## Changes

- 审计 Prompt 输入完整 Canon entity ID、kind、name，以及经确定性前缀重放得到的
  `state_before_batch`。
- 地点效果仅允许 key event 明确跨越两个不同的现有 Canon location ID；同一
  Canon 地点内的西岸、深处等场景移动必须返回空数组，不得创建子地点。
- 审计 parser 同时验证非空 `from_location_id` 与 `to_location_id` 均来自 Canon；
  后续 object-creation 与同地点移动规则仍由原 validator fail closed。
- 新增 Prompt 绑定和双端虚构地点回归；没有新增自然语言词表、依赖或数据库变更。

## Validation

- 正式 Revision `50c17e57612c46499b060f7615cfbf1f` 通过
  `resume-async` 创建 Task `6634` / business ID
  `a0a7a21f85e54de993521a6abf530063`。
- Invocation `1348`–`1353` 均为 `deepseek-v4-pro` 且
  `finish_reason=stop`；合计 input 42038、cache 12032、output 48700 tokens。
- 第 1–8 章语义审计 `1350` 通过并 checkpoint 8 章；第 9–16 章首次审计
  `1352` 触发 typed-effect 定点补丁，第二次审计 `1353` 虚构
  `salt-mirror-west-coast` 和 `salt-marsh-deep`。Canon 仅有
  `salt-mirror-island`，parser 正确以
  `语义审计地点引用无效: ev-10-1` fail closed；Task 6634 失败且 0 正文章。
- `pytest tests/unit/test_story_novel_plan_semantic_audit.py -q --no-cov`
  -> 9 passed。
- `pytest tests/unit/test_story_novel_*.py -q --no-cov`
  -> 386 passed, 1 skipped。
- 精确路径 `isort --profile=black --check-only` 和 `black --check`
  -> passed。
- `python scripts/check_repo_contracts.py --mode diff ...`
  -> passed；源码 249 行，测试 220 行。
- `git diff --check` -> passed。

## Next Steps

- 构建并重载正式 backend/worker，只对同一 Revision 调用一次正式 Resume。
- 计划 48/48 语义审计通过后进入正文；至少两章 ready 时执行正式取消、hash
  快照和 Resume，再生成至 48/48。
- 完成连续性检查、GPT-5.6 分批与全书审读、审批、Canon 提升和 artifact 归档。

## Linked Commits

- 本记录与 Canon location 审计修复位于同一原子提交。
