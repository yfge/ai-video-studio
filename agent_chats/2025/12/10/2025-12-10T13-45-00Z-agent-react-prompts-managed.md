---
id: 2025-12-10T13-45-00Z-agent-react-prompts-managed
date: 2025-12-10T13:45:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, agent, prompts]
related_paths:
  - ai-pic-backend/app/services/episode_agent.py
  - ai-pic-backend/app/services/story_agent.py
  - ai-pic-backend/app/prompts/templates/episode_plan_repair.txt
  - ai-pic-backend/app/prompts/templates/episode_plan_repair.yaml
  - ai-pic-backend/app/prompts/templates/story_outline_repair.txt
  - ai-pic-backend/app/prompts/templates/story_outline_repair.yaml
  - ai-pic-backend/app/prompts/templates.py
summary: "Route story/episode ReAct repairs through PromptManager with schema/missing-field context and clearer node flow."
---

## User Prompt

- “改成多结点… valid 里给出缺失的字段 ，prompt 里要有 ，要进行尽可能精准的修复”
- “同时要使用prompt_manager 来管理react 提示词”

## Goals

- Make LangGraph agents explicitly multi-node and delegate repair prompts to PromptManager-managed templates.
- Surface missing-field details in repair prompts for more precise JSON fixes.

## Changes

- Episode/story agents now use `plan -> repair` nodes; repair loops validate/repair up to 3 passes, logging parse/schema failures and passing missing-field hints plus original prompts into template-driven repair prompts.
- Added PromptTemplate enums and YAML/TXT templates for `episode_plan_repair` and `story_outline_repair`, including missing-field listings and schema context.
- Enhanced episode repair template variables to carry missing_fields.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_story_parser.py -q`
- Chrome MCP: not run (backend-only change, no live stack here).

## Next Steps

- Run end-to-end story/episode generation to confirm repairs reduce schema failures and logs show missing-field hints.
- Consider extending the same pattern to storyboard agent if needed.

## Linked Commits

- pending
