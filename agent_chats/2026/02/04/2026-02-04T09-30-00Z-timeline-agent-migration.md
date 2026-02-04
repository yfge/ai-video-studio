---
id: 2026-02-04T09-30-00Z-timeline-agent-migration
date: 2026-02-04T09:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, agent-migration, P2]
related_paths:
  - ai-pic-backend/app/services/timeline_agent/__init__.py
  - ai-pic-backend/app/services/timeline_agent/react_agent.py
  - ai-pic-backend/app/services/audio/dialogue_processing/segment_intelligent_planner.py
  - ai-pic-backend/tests/unit/services/timeline_agent/test_react_agent.py
  - tasks-agent-fix.md
summary: "Migrated Timeline Agent from LangGraph to ReactAgentBase framework"
---

## User Prompt

User requested full rewrite (option 1) to migrate Timeline Agent to the new ReactAgentBase framework.

## Goals

1. Create TimelineReactAgent class inheriting from ReactAgentBase
2. Implement _generate, _parse_result, _validate, _refine_input methods
3. Integrate RepairMonitor for success rate tracking
4. Update production code to use new agent
5. Add comprehensive unit tests

## Changes

### New Files Created

1. **`app/services/timeline_agent/react_agent.py`** (~350 lines)
   - `TimelineReactAgent(ReactAgentBase[TimingPlan])`: Main agent class
   - `compute_timing()`: Public API matching original interface
   - `_generate()`: LLM call with context building
   - `_parse_result()`: JSON parsing into TimingPlan
   - `_validate()`: Constraint validation (gap ranges, avg gap, rhythm)
   - `_refine_input()`: Error feedback for repair
   - `_compute_fallback()`: Rule-based fallback timing
   - Integrated `RepairMonitor` for success tracking
   - Integrated `FailurePatternMatcher` for error classification

2. **`tests/unit/services/timeline_agent/test_react_agent.py`** (17 tests)
   - TestTimelineReactAgent: Agent initialization, compute_timing flow
   - TestParseResult: JSON parsing, edge cases
   - TestValidation: Constraint validation
   - TestRefineInput: Error feedback
   - TestFallback: Rule-based timing

### Updated Files

1. **`app/services/timeline_agent/__init__.py`**
   - Added export for `TimelineReactAgent`
   - Updated docstring to describe both implementations

2. **`app/services/audio/dialogue_processing/segment_intelligent_planner.py`**
   - Changed import from `TimelineLangGraphAgent` to `TimelineReactAgent`
   - Production code now uses new framework

3. **`tasks-agent-fix.md`**
   - Marked P2.13.3 as complete
   - P2 progress: 13/15 → 14/15

## Architecture Changes

### Before (LangGraph)
```
TimelineLangGraphAgent
├── StateGraph with 6 nodes
├── analyze_scene → think_timing → propose_gaps → validate_rhythm → adjust/finalize
├── Manual retry loop with MAX_REPAIR_ATTEMPTS
└── Custom error handling
```

### After (ReactAgentBase)
```
TimelineReactAgent(ReactAgentBase[TimingPlan])
├── _generate(): LLM call
├── _parse_result(): JSON → TimingPlan
├── _validate(): Constraint checking
├── _refine_input(): Error feedback
├── Automatic retry loop from base class
├── RepairMonitor integration
└── FailurePatternMatcher for error classification
```

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/timeline_agent/test_react_agent.py -v
# Result: 17 passed

python -c "from app.services.audio.dialogue_processing.segment_intelligent_planner import plan_scene_segments_intelligent; print('Import successful')"
# Result: Import successful
```

## Next Steps

1. P2.13.4: Migrate Script Agent to new framework (last remaining task)
2. Browser test to validate timeline generation in production flow

## Linked Commits

(To be added after commit)
