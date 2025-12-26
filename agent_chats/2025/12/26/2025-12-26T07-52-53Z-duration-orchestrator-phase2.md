---
id: 2025-12-26T07-52-53Z-duration-orchestrator-phase2
date: 2025-12-26T07:52:53Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, duration-orchestrator, script-agent, langgraph]
related_paths:
  - ai-pic-backend/app/services/script_agent.py
  - ai-pic-backend/app/services/duration_orchestrator/nodes/generate_dialogue.py
  - ai-pic-backend/app/services/duration_orchestrator/nodes/__init__.py
  - ai-pic-backend/tests/unit/services/duration_orchestrator/test_generate_dialogue.py
  - ai-pic-backend/tests/unit/services/test_script_agent_word_count.py
summary: "Duration Orchestrator Phase 2: Integrated word count constraints into ScriptLangGraphAgent and implemented generate_dialogue node"
---

## User Prompt

Continued from previous session. Phase 1 of Duration Orchestrator was completed with 26 passing tests. Continue with Phase 2 - modifying ScriptLangGraphAgent to support target_word_count constraint.

## Goals

1. Modify `ScriptLangGraphAgent` to accept `scene_budgets` parameter
2. Integrate word count constraints into dialogue generation prompt
3. Implement `generate_dialogue` node for Duration Orchestrator
4. Write comprehensive unit tests for Phase 2 changes

## Changes

### 1. Modified `app/services/script_agent.py`

- Added import for `SceneBudget` from duration_orchestrator state
- Added `scene_budgets: Optional[List[SceneBudget]] = None` parameter to `generate()` method
- Added `_build_word_count_constraints()` helper method:
  - Renders word count constraint template for each scene budget
  - Uses `prompt_manager.render_prompt()` with `SCRIPT_WORD_COUNT_CONSTRAINT` template
  - Includes retry hints when `attempt_count > 0`
- Modified `write_dialogues` node to append word count constraints to prompt when `scene_budgets` provided

### 2. Created `app/services/duration_orchestrator/nodes/generate_dialogue.py`

New LangGraph node for dialogue generation:
- `generate_dialogue_node()`: Calls ScriptLangGraphAgent with scene budgets
  - Updates budget status to IN_PROGRESS
  - Increments attempt_count
  - Filters generated dialogues by scene_number
  - Calculates actual_word_count using `count_dialogue_words()`
- `should_proceed_to_tts()`: Router function returning "tts", "retry", or "failed"

### 3. Updated `app/services/duration_orchestrator/nodes/__init__.py`

- Exported new functions: `generate_dialogue_node`, `should_proceed_to_tts`
- Exported additional routing functions: `should_proceed_to_generation`, `should_commit_or_retry`, `check_all_scenes_done`

### 4. Created Test Files

#### `tests/unit/services/duration_orchestrator/test_generate_dialogue.py`
- `TestGenerateDialogueNode`: 8 test cases
  - Successful generation
  - Generation with retry hint
  - Missing script_agent error handling
  - Generation failure handling
  - Index out of bounds
  - Status update to in_progress
  - Word count calculation
  - Filtering dialogues by scene_number

- `TestShouldProceedToTTS`: 4 test cases
  - Proceed to TTS with dialogues
  - Retry without dialogues
  - Failed after max retries
  - Failed with invalid index

#### `tests/unit/services/test_script_agent_word_count.py`
- `TestBuildWordCountConstraints`: 5 test cases
  - Empty budgets returns empty string
  - Single budget constraint
  - Multiple budget constraints
  - Retry hint included
  - No retry hint for first attempt

- `TestGenerateMethodSignature`: 2 test cases
  - Accepts scene_budgets parameter
  - scene_budgets is optional

## Validation

All 45 unit tests passed:

```
tests/unit/services/duration_orchestrator/test_budget_allocation.py: 26 passed
tests/unit/services/duration_orchestrator/test_generate_dialogue.py: 12 passed
tests/unit/services/test_script_agent_word_count.py: 7 passed
```

Import verification:
```python
from app.services.script_agent import ScriptLangGraphAgent  # OK
from app.services.duration_orchestrator.nodes import generate_dialogue_node  # OK
```

## Next Steps

1. **Phase 3**: Implement TTS trial node (`tts_trial_node`)
   - Call TTS service to get actual duration
   - Update `actual_duration_seconds` in budget

2. **Phase 4**: Implement commit/rebalance nodes
   - `commit_scene_node`: Finalize scene and rebalance remaining budgets
   - `prepare_retry_node`: Generate adjustment hints for failed validations

3. **Phase 5**: Assemble StateGraph
   - Wire all nodes together
   - Implement routing logic between nodes

4. **Phase 6**: API integration
   - Create `/api/v1/episodes/{id}/duration-orchestrate` endpoint

## Linked Commits

(To be added after git commit)
