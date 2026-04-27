---
id: 2026-04-27T09-44-40Z-langgraph-completeness
date: "2026-04-27T09:44:40Z"
participants: [human, codex]
models: [codex]
tags: [backend, langgraph, storyboard, script, docs]
related_paths:
  - ai-pic-backend/app/services/script_agent.py
  - ai-pic-backend/app/services/storyboard/pipeline/
  - scripts/generate_agent_graphs.py
  - docs/agent_graphs/
summary: "Fixed ScriptLangGraph retry routing, made StoryboardPipeline an explicit plan graph, and aligned graph docs."
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN: 生成链路 LangGraph 完备性整改计划。

## Goals

- Fix ScriptLangGraphAgent stale REACT retry routing after successful retry.
- Make StoryboardPipeline an explicit StateGraph pipeline with a generate_plan node and plan-scoped frame generation.
- Keep Story/Episode compatibility names while documenting them as structured repair loops, not active LangGraph diagrams.
- Keep generated graph docs, registry, and README references aligned.
- Add focused regression tests for Script retry, StoryboardPipeline plan flow, and graph-doc drift.

## Changes

- Added shared graph helpers for error routing, bounded flag reset, reasoning updates, and end-on-error routing.
- Updated ScriptLangGraphAgent to clear `react_needs_retry` on pass/max/fill paths and route scene/dialogue errors to graph termination before spending more tokens.
- Moved ScriptAgent direct lookups into `app/repositories/script_lookup_repository.py` so the touched service file remains within repo contracts.
- Split StoryboardPipeline into small execution, plan, and validation mixins.
- Added StoryboardPipeline `generate_plan` node, preserved model/provider/max_frames in runtime state, generated frames from explicit plan scenes, and forced direct fallback calls to `prefer_graph=False`.
- Regenerated real StateGraph diagrams and removed conceptual Story/Episode LangGraph diagrams.
- Updated README and README_EN to list only real StateGraph-backed generation diagrams and mark Timeline legacy / Duration experimental.

## Validation

- `python -m py_compile ai-pic-backend/app/services/script_agent.py ai-pic-backend/app/repositories/script_lookup_repository.py ai-pic-backend/app/services/agent_core/graph_helpers.py ai-pic-backend/app/services/agent_core/__init__.py ai-pic-backend/app/services/storyboard/pipeline/storyboard_pipeline.py ai-pic-backend/app/services/storyboard/pipeline/execution_mixin.py ai-pic-backend/app/services/storyboard/pipeline/plan_mixin.py ai-pic-backend/app/services/storyboard/pipeline/validation_mixin.py scripts/generate_agent_graphs.py`
- `cd ai-pic-backend && pytest tests/unit/services/test_script_agent_langgraph_early_exit.py tests/unit/test_storyboard_reasoner.py tests/unit/services/storyboard/pipeline/test_storyboard_pipeline.py tests/unit/services/storyboard/pipeline/test_storyboard_pipeline_plan_graph.py tests/unit/services/test_agent_graph_docs.py -q`
  - Result: `29 passed, 44 warnings in 0.35s`
- `python scripts/check_repo_docs.py`
  - Result: `[check_repo_docs] ok`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
  - Result: `[check_repo_contracts] ok (diff)`

## Next Steps

- No follow-up required for this phase.
- Remaining broader debt: Story/Episode class names and historical `generation_method` values remain compatibility artifacts by design.

## Linked Commits

- Not committed in this session.
