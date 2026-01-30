---
id: 2026-01-28T05-10-40Z-storyboard-langgraph-unify
date: 2026-01-28T05:10:40Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, frontend, storyboard, langgraph, tasks]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/services/ai/storyboard_generation.py
  - ai-pic-backend/app/services/ai/storyboard_plan.py
  - ai-pic-backend/app/services/storyboard/langgraph_utils.py
  - ai-pic-backend/app/services/storyboard_reasoner.py
  - ai-pic-backend/app/services/storyboard/storyboard_prompt_utils.py
  - ai-pic-backend/app/services/task_agent_run/builders_script_ops.py
  - ai-pic-backend/tests/unit/test_storyboard_reasoner.py
  - ai-pic-frontend/src/components/features/tasks/TaskDetails.tsx
  - docs/TESTING_GUIDE.md
  - tasks.md
summary: "Unified storyboard LangGraph pipeline with plan/trace audit and tasks UI details"
---

## User Prompt

继续处理 P1 任务，完成「分镜 LangGraph 管线统一（规划+生成）」，要求可审计、任务页可查看，并按规范验证。

## Goals

- 统一分镜生成走 LangGraph 规划→生成→校验/修复管线，并输出可审计轨迹
- 同步落库 plan/frames/usage/reasoning_trace，并在任务页展示
- 更新测试指引与任务看板状态

## Changes

- 拆出 `langgraph_utils`，复用镜头/运镜/构图循环与计划规范化、缺口检测
- 重构 `StoryboardReActReasoner` 为 LangGraph 规划→生成→校验→修复→终审流程并输出 trace/plan/usage
- `generate_storyboard` 默认优先 LangGraph，返回 plan/fixes/trace/usage
- `scripts_legacy` 分镜入口统一走 LangGraph，落库 `storyboard_plan` 与 `meta` 审计字段
- 任务 agent_run 补充 storyboard plan/frames/trace/usage/fixes 输出
- 任务详情 UI 展示 reasoning_trace、plan、frames、plan_fixes
- 更新 `TESTING_GUIDE` 与 `tasks.md` 状态

## Validation

- `cd ai-pic-backend && pytest` ❌ 启动后长时间无进展，已中止（仅看到收集 1070 tests；无完成报告）
- `cd ai-pic-backend && pytest tests/unit/test_storyboard_reasoner.py` ✅ 3 passed (warnings only)
- `cd ai-pic-frontend && npm run lint` ✅ (7 warnings, 0 errors)
- `pre-commit run --all-files` ❌ `trailing-whitespace` 触发大量历史文件改动且 `ruff`/`backend-pytest` 失败（已还原非本次文件）
- `./docker/build_prod_images.sh` ✅ backend/frontend 镜像构建并推送完成（tag: ae7a4a4）
- Chrome E2E ❌ 尝试 `http://localhost:8089/login` 登录（geyunfei/Gyf@845261），界面提示 “Failed to fetch”，无法进入任务页

## Next Steps

- 在 Chrome 跑分镜生成 E2E：/episodes/{id}/storyboard → 生成分镜 → /tasks 查看 plan/trace
- 处理/分流 pre-commit 的全仓 trailing whitespace（单独任务）
- 逐步修复 pytest 现有失败或拆分成可运行子集

## Linked Commits

- TBD
