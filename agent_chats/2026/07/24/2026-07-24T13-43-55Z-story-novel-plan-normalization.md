---
id: 2026-07-24T13-43-55Z-story-novel-plan-normalization
date: "2026-07-24T13:43:55Z"
participants: [user, codex]
models: [gpt-5.6-sol]
tags: [backend, story, novel, planning, canon, future-gate]
related_paths:
  - ai-pic-backend/app/services/story/story_novel_plan_normalizer.py
  - ai-pic-backend/app/services/story/story_novel_planning_phases.py
  - ai-pic-backend/app/services/story/story_novel_future_claims.py
  - ai-pic-backend/tests/unit/test_story_novel_plan_normalizer.py
  - ai-pic-backend/tests/unit/test_story_novel_planning_repair.py
  - ai-pic-backend/tests/unit/test_story_novel_future_claim_semantics.py
summary: Normalize provable planning aliases and redundant owner-carried object movements while failing closed on exact premature future events.
---

## User Prompt

完成 Canon 状态门禁与长篇小说质量闭环，并通过系统正式 API、真实 MySQL
和实际模型完成全新 48 章生成、断点恢复及 GPT-5.6 全书验收。

## Goals

- 让模型输出的章节规划在进入严格 schema 和确定性状态验证前，仅修复可证明的字段别名。
- 消除人物移动已经携带其物件时重复声明物件移动造成的伪状态不连续。
- 不放宽 Canon、状态、地点、所有权、未来事件或里程碑验证规则。

## Changes

- 在章节规划 payload 中仅将非空 `location_transition.reason` 兼容为缺失的 `means`；
  两者均缺失时继续由 Pydantic fail closed。
- 仅当物件当前所有者、possessions、人物与物件起点以及共同终点全部精确匹配时，
  删除被人物移动确定性涵盖的重复物件移动。
- 在真实 `_parse_plan` 路径接入 payload 规范化，并增加别名、缺失字段、
  所有者携带和不匹配目标的回归测试。
- 增加未来事件逐句精确完成检查：即使未来事件没有“确认/揭露”等措辞，
  正文逐字完成该事件仍会 fail closed；传言、假设和否认不误报。

## Validation

- `pytest tests/unit/test_story_novel_plan_normalizer.py tests/unit/test_story_novel_planning_repair.py -q --no-cov`
  -> 12 passed。
- `pytest tests/unit/test_story_novel_*.py -q --no-cov`
  -> 350 passed, 1 skipped（规划补丁格式化后基线）。
- `pytest tests/unit/test_story_novel_future_claim_semantics.py -q --no-cov`
  -> 7 passed。
- 未来事件门禁加入后再次运行
  `pytest tests/unit/test_story_novel_*.py -q --no-cov`
  -> 352 passed, 1 skipped。
- 精确四文件 `pre-commit run isort --files ...` -> passed。
- 精确四文件 `pre-commit run black --files ...` -> passed。
- `python scripts/check_repo_contracts.py --mode diff <四个路径>` -> ok。
- `git diff --check` -> passed。

## Next Steps

- 处理代码审查确认的未来不可逆事件漏检，再加载当前源码进入唯一合法 Revision 的正式生成。
- 至少两章后执行正式 cancel/hash snapshot/resume，最终完成 48/48 与 GPT-5.6 审读。

## Linked Commits

- Pending
