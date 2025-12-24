---
id: 2025-12-24T18-00-00Z-script-agent-review-step
date: 2025-12-24T18:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, script-agent, langgraph, quality-improvement]
related_paths:
  - ai-pic-backend/app/services/script_agent.py
  - ai-pic-backend/app/prompts/templates.py
  - ai-pic-backend/app/prompts/templates/script_dialogues.txt
  - ai-pic-backend/app/prompts/templates/script_review.txt
summary: "Add review step to script agent for dialogue/stage_direction classification"
---

## User Prompt

User reported: "有一些对白落在舞台指令中，要加react进行调整和检查，保证剧本质量"

Example problem from Scene 2:
- "嗯？电流读数异常波动。" was classified as stage_direction instead of dialogue
- "搞什么……电磁干扰？备用电源没启动吗？" was classified as stage_direction instead of dialogue

## Goals

1. Add a review/react step to the LangGraph script generation pipeline
2. Improve prompts to better classify dialogues vs stage_directions
3. Ensure script quality by catching and fixing misclassifications

## Changes

### Backend

**`ai-pic-backend/app/services/script_agent.py`**

Added new `review_classification` node to the LangGraph pipeline:
- Pipeline now: `scene_plan` → `dialogue` → `review` → `assemble`
- Review node uses AI to check for misclassified content
- Detects dialogues incorrectly placed in stage_directions (questions, exclamations, speech patterns)
- Moves misclassified items between arrays
- Logs corrections for debugging
- Gracefully handles failures (keeps original data if review fails)

**`ai-pic-backend/app/prompts/templates.py`**

- Added `SCRIPT_REVIEW = "script_review"` to PromptTemplate enum
- Added mapping to TEMPLATE_CATEGORIES

**`ai-pic-backend/app/prompts/templates/script_dialogues.txt`**

Enhanced prompt with explicit classification rules:
- Added clear examples of what belongs in dialogues vs stage_directions
- Added "common errors to avoid" section
- Emphasized that questions, exclamations, and speech-like content should be dialogues

**`ai-pic-backend/app/prompts/templates/script_review.txt`** (new file)

New prompt template for the review step:
- Clear judgment criteria for dialogues vs stage_directions
- Examples of correct classification
- Common error patterns to detect
- Output includes corrections list for logging

## Validation

1. Backend import test: `python -c "from app.services.script_agent import ScriptLangGraphAgent"` - Success
2. Prompt template test: `prompt_manager.render_prompt(PromptTemplate.SCRIPT_REVIEW.value, ...)` - Success
3. Browser verification: Confirmed issue exists in current script (Scene 2 has dialogue in stage_directions)

## Next Steps

1. Test script generation with review step enabled
2. Monitor correction logs to verify review effectiveness
3. Consider adding confidence scores to corrections
4. May need to fine-tune review prompt based on real-world results

## Linked Commits

- 170d3d6 feat(backend): add review step to script agent for dialogue classification
