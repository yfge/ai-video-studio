---
id: 2025-12-26T12-00-00Z-script-agent-duration-aware-react
date: 2025-12-26T12:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, script-agent, duration-control, react]
related_paths:
  - ai-pic-backend/app/services/script_agent.py
  - ai-pic-backend/app/prompts/templates/script_scenes.txt
  - ai-pic-backend/app/prompts/templates/script_scenes.yaml
summary: "Refactored script agent with duration-aware scene planning and REACT validation"
---

## User Prompt

User requested: "整体重构剧本生成的agent 吧，把时间作为一个重点考虑，从一开始进行场景划分时就要考虑每个场景的时间，同时也要计算好对白和非对白时间，在对白生成后要进行react 检查"

Translation: Completely refactor the script generation agent with time as a priority:
1. Consider scene time from the scene planning stage
2. Calculate dialogue vs non-dialogue time budgets
3. Add REACT validation after dialogue generation

## Goals

1. Update `script_scenes.txt` template to request duration per scene
2. Add `dialogue_ratio` field to distinguish dialogue vs non-dialogue time
3. Modify `ScriptLangGraphAgent` to compute scene budgets from LLM-planned durations
4. Add REACT validation node after dialogue generation with retry loop
5. Ensure all existing tests pass

## Changes

### 1. script_scenes.txt - Duration-aware template

Updated template to:
- Accept `duration_minutes` variable
- Request `estimated_duration_seconds` per scene from LLM
- Request `dialogue_ratio` (0.0-1.0) indicating dialogue vs action ratio
- Guide LLM to ensure total scene durations sum to episode duration

```yaml
## 时长约束（重要）

剧集目标时长：{{ duration_minutes }} 分钟

你必须为每个场景分配合理的时长，确保：
1. 所有场景时长之和 ≈ {{ duration_minutes * 60 }} 秒
2. 每个场景时长在 10-120 秒范围内
3. 每个场景需标注"对白占比"（dialogue_ratio）
   - 纯对白场景：0.8-0.95
   - 混合场景：0.5-0.8
   - 动作/转场为主：0.2-0.5
```

### 2. script_agent.py - New helper methods

**`_compute_budgets_from_scenes()`** (lines 88-161):
- Computes `SceneBudget` objects from LLM-planned scenes
- Uses LLM-assigned `estimated_duration_seconds` and `dialogue_ratio`
- Falls back to equal distribution if LLM didn't assign durations
- Calculates word count: `dialogue_seconds * WORDS_PER_SECOND`

**`_estimate_dialogue_duration()`** (lines 163-185):
- Estimates duration from dialogue content length
- Filters by scene_number if provided

**`_validate_scene_duration()`** (lines 187-209):
- Checks if actual duration is within ±15% tolerance
- Returns (is_valid, rejection_reason) tuple

### 3. script_agent.py - Updated plan_scenes node

- Passes `duration_minutes` to template
- Includes `estimated_duration_seconds` and `dialogue_ratio` in JSON schema
- After LLM response, computes scene budgets via `_compute_budgets_from_scenes()`
- Stores `computed_budgets` in state for downstream nodes

### 4. script_agent.py - REACT validation node

**`react_validate_duration()`** (lines 456-548):
- Validates each scene's dialogue duration against budget
- If outside ±15% tolerance and attempts < 3: marks for retry
- Updates budget with `adjustment_hint` for next attempt
- Returns `react_needs_retry=True` to trigger retry loop

**`should_retry_dialogues()`** (lines 550-554):
- Conditional edge function
- Routes to "dialogue" node if retry needed, else to "review"

### 5. Graph flow update

```
scene_plan → dialogue → react_validate → (conditional) → review → assemble
                              ↓                ↓
                        (retry needed)    (passed)
                              ↓                ↓
                           dialogue        review
```

## Validation

1. **Import Check**: `from app.services.script_agent import ScriptLangGraphAgent` - OK
2. **Script Agent Tests**: 7/7 passed
3. **Duration Orchestrator Tests**: 26/26 passed

## Architecture Summary

**Before**:
```
scene_plan (no duration awareness)
    ↓
write_dialogues (word constraints from external budgets)
    ↓
review_classification
    ↓
assemble
```

**After**:
```
scene_plan (with duration_minutes, outputs estimated_duration_seconds + dialogue_ratio)
    ↓
compute_budgets (from LLM-assigned durations, considers dialogue_ratio)
    ↓
write_dialogues (with computed budgets)
    ↓
react_validate_duration (±15% tolerance check)
    ↓ (retry if failed, max 3 attempts)
review_classification
    ↓
assemble
```

**Key Improvements**:
1. Duration considered from scene planning stage (not post-hoc)
2. LLM allocates time per scene based on dramatic importance
3. `dialogue_ratio` separates dialogue from action/transition time
4. REACT validation loop ensures duration targets are met
5. Up to 3 retry attempts with specific adjustment hints

## Next Steps

1. Deploy and test with real episode regeneration
2. Verify logs show computed budgets and REACT validation
3. Fine-tune constants if needed (tolerance, retry count)

## Linked Commits

- (pending) feat(script-agent): duration-aware scene planning with REACT validation
