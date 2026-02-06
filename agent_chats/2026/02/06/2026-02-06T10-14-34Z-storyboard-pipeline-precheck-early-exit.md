---
id: 2026-02-06T10-14-34Z-storyboard-pipeline-precheck-early-exit
date: "2026-02-06T10:14:34Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, storyboard, langgraph]
related_paths:
  - ai-pic-backend/app/services/storyboard/pipeline/storyboard_pipeline.py
  - ai-pic-backend/tests/unit/services/storyboard/pipeline/test_storyboard_pipeline.py
  - ai-pic-backend/tests/unit/services/__init__.py
summary: "Short-circuit StoryboardPipeline LangGraph execution after precheck failure to reduce wasted generation."
---

## User Prompt

- "检查所有生成的langgraph 看有没有针对性的需要改进的地方来保证 生成质量"
- "2. 先修 StoryboardPipeline 的 LangGraph precheck 早停（直接提升线上生成质量和成本）"

## Goals

- Stop LangGraph execution immediately after precheck failure (avoid wasted generation/cost).
- Add regression coverage for the precheck early-exit path.
- Keep CI-style validation gates (tests + prod image build) green.

## Changes

- Updated `StoryboardPipeline._execute_langgraph()` to conditionally route after `precheck`:
  - If `pipeline_state.has_errors` is set by precheck validation, route to `finalize`.
  - Otherwise continue to `validate_plan` and downstream nodes.
- Added unit test asserting LangGraph does not run `validate_plan` when precheck fails.
- Fixed pytest test package collection by adding `ai-pic-backend/tests/unit/services/__init__.py` and updated an existing validator-count assertion to match current pipeline configuration.

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/storyboard/pipeline/test_storyboard_pipeline.py -q`
- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`
- Chrome (MCP) E2E:
  - Login: `http://localhost:8089/login` as `geyunfei`.
  - Go to `http://localhost:8089/episodes/124/storyboard`, click "生成全部场景" to create a storyboard generation task.
  - Go to `http://localhost:8089/tasks`, open task details for task `5941`, confirm status "已完成" and `Agent 执行轨迹` includes `reasoning_trace` with `precheck_started` / `precheck_completed` and final `task_status: completed`.

## Next Steps

- Add an E2E scenario that intentionally fails precheck to confirm the early-exit behavior in the async task runner path.
- Audit other LangGraph pipelines for similar precheck short-circuit opportunities (cost + quality).

## Linked Commits

- (this commit)
