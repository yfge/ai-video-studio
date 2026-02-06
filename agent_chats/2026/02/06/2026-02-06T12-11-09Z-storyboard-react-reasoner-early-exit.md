---
id: 2026-02-06T12-11-09Z-storyboard-react-reasoner-early-exit
date: "2026-02-06T12:11:09Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, langgraph, storyboard]
related_paths:
  - ai-pic-backend/app/services/storyboard_reasoner.py
  - ai-pic-backend/app/services/storyboard/langgraph_utils.py
  - ai-pic-backend/tests/unit/test_storyboard_reasoner.py
summary: "Add early-exit + scope filtering to StoryboardReActReasoner to reduce wasted calls and improve output quality."
---

## User Prompt

- 检查所有生成的 LangGraph，看看有没有针对性的需要改进的地方来保证生成质量。
- 先修 StoryboardPipeline 的 LangGraph precheck 早停；然后补 StoryboardReActReasoner 的 LangGraph precheck 早停。

## Goals

- 在 `StoryboardReActReasoner` 图内尽早识别「无可生成场景 / scope 无效」并早停，减少无意义 LLM 调用与失败链路成本。
- 确保后续生成与校验只针对 `scene_scope` 内场景，避免越界/跑偏导致的质量问题。
- 增加单测覆盖关键早停与 scope 过滤路径，避免回归。

## Changes

- `ai-pic-backend/app/services/storyboard_reasoner.py`
  - `select` 节点新增 scope 计算与错误态（`missing_scenes` / `scene_scope_empty`）。
  - `critique` 节点在 `normalize_plan_outlines` 后按 `scene_scope` 过滤 plan 场景，确保生成/校验只覆盖目标场景。
  - `select` / `plan` 节点后新增 LangGraph conditional routing：一旦出现 `state["error"]`，直接 `END`，避免后续无意义步骤。
- `ai-pic-backend/app/services/storyboard/langgraph_utils.py`
  - 新增 `compute_available_scenes` / `compute_scene_scope` / `filter_plan_to_scope`，集中处理 scope 计算与 plan 过滤逻辑。
- `ai-pic-backend/tests/unit/test_storyboard_reasoner.py`
  - 扩展 DummyService：记录 `plan_calls`，便于断言「早停时不触发 plan」。
  - 新增用例：`selected_scenes=None` 且 `script.scenes=[]` 时不调用 plan；plan 含多场景但仅生成 scope 内场景。
  - 更新 plan 失败用例：确保 plan 被调用且不会触发按场景生成（提前结束）。

## Validation

- Unit tests:
  - `cd ai-pic-backend && pytest tests/unit/test_storyboard_reasoner.py -q`
- Build:
  - `./docker/build_prod_images.sh`
- Chrome E2E (Docker dev + Nginx):
  - 登录 `http://localhost:8089/login`（`geyunfei` / `Gyf@845261`）。
  - 打开 `http://localhost:8089/episodes/124/storyboard`，点击「生成全部场景」（`use_plan=true`）。
  - 打开 `http://localhost:8089/tasks`，确认 `storyboard_generation` 任务完成：
    - TaskID: `5944`
    - `agent_run.frames`: `35` 帧
    - `agent_run.reasoning_trace` 非空

## Next Steps

- 若希望更强可审计性：将 `plan` / `plan_fixes`（以及 provider/model/usage）补齐到 `agent_run` 展示（当前主要展示 frames + reasoning_trace）。
- 如线上仍出现越界 scene_number：在入口（UI/接口）层增加对 `selected_scenes` 的一致性校验与提示。

## Linked Commits

- TBD

