---
id: 2026-02-06T10-41-04Z-script-agent-langgraph-early-exit
date: "2026-02-06T10:41:04Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, langgraph, quality, cost]
related_paths:
  - ai-pic-backend/app/services/script_agent.py
  - ai-pic-backend/tests/unit/services/test_script_agent_langgraph_early_exit.py
summary: "Skip ScriptLangGraphAgent LLM calls when upstream planning fails to reduce waste and improve failure handling."
---

## User Prompt
检查所有生成的 langgraph 看有没有针对性的需要改进的地方来保证生成质量；先修 StoryboardPipeline 的 LangGraph precheck 早停。

## Goals
- Reduce wasted LLM calls when ScriptLangGraphAgent upstream nodes fail (cost + quality).
- Keep success path unchanged while making failure paths cheaper and more deterministic.
- Add a unit test to lock the behavior.

## Changes
- Added early-exit guards in ScriptLangGraphAgent LangGraph nodes:
  - `write_dialogues`: skip generation if `state["error"]` is set; mark missing scenes as `error=missing_scenes`.
  - `review_classification`: skip review if `state["error"]` is set, or if both dialogues and stage directions are empty.
- Added a unit test asserting that when scene planning fails, the agent makes only one LLM call (scene plan) and returns `None`.

## Validation
- `cd ai-pic-backend && pytest tests/unit/services/test_script_agent_langgraph_early_exit.py -q`
- `cd ai-pic-backend && pytest tests/unit/services/test_script_agent_*.py -q`
- `./docker/build_prod_images.sh`
- Chrome (MCP) E2E:
  - Login as `geyunfei`.
  - Open `http://localhost:8089/episodes/124/workspace?tab=script` and click "重新生成剧本" for Script ID `126`.
  - On `http://localhost:8089/tasks`, observe Task ID `5943` completed with result `script:127` (provider `deepseek`, model `deepseek-chat`).

## Next Steps
- Audit remaining LangGraph-based generators for similar upstream-error short-circuits (avoid downstream LLM calls when `state.error` exists).
- Consider graph-level conditional routing to `END` on fatal errors to reduce non-LLM overhead as well.

## Linked Commits
- (this commit) fix(backend): early-exit script langgraph nodes on upstream error
