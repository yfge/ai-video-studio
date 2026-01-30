---
id: 2025-12-26T09-45-00Z-duration-orchestrator-phase4
date: 2025-12-26T09:45:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, duration-orchestrator, langgraph, state-machine]
related_paths:
  - ai-pic-backend/app/services/duration_orchestrator/agent.py
  - ai-pic-backend/app/services/duration_orchestrator/__init__.py
  - ai-pic-backend/tests/unit/services/duration_orchestrator/test_agent.py
summary: "Duration Orchestrator Phase 4: Assembled LangGraph StateGraph with all nodes and conditional edges"
---

## User Prompt

Continue with Phase 4 of Duration Orchestrator - Assemble LangGraph StateGraph.

## Goals

1. Create `agent.py` with complete `DurationOrchestratorAgent` class
2. Wire all nodes from Phase 1-3 with conditional edges
3. Implement the main orchestration loop: allocate → generate → tts → validate → (commit|retry)
4. Write integration tests for scene loop

## Changes

### 1. Created `app/services/duration_orchestrator/agent.py`

Complete `DurationOrchestratorAgent` implementation with LangGraph StateGraph:

- **`DurationOrchestratorAgent` class**:

  - `__init__()`: Accepts `script_agent`, `tts_service`, and `use_actual_tts` flag
  - `_build_graph()`: Constructs StateGraph with all nodes and edges
  - `orchestrate()`: Main async method to execute end-to-end duration control

- **StateGraph Structure**:

  ```
  allocate_budget
      ↓
  generate_dialogue ←─────────────┐
      ↓                           │
  tts_trial                       │
      ↓                           │
  validate_duration               │
      ↓                           │
  ┌───┴───┐                       │
  │       │                       │
  commit   prepare_retry ─────────┘
    │
    ↓
  ┌───┴───┐
  │       │
  continue assemble
  (loop)    ↓
           END
  ```

- **Conditional Edge Routing**:

  - `allocate_budget` → `generate_dialogue` (if scenes exist) or `END` (if empty/failed)
  - `generate_dialogue` → `tts_trial` (if success) or retry/failed
  - `tts_trial` → `validate_duration` (always)
  - `validate_duration` → `commit_scene` (if within tolerance) or `prepare_retry`
  - `prepare_retry` → `generate_dialogue` (loop for retry)
  - `commit_scene` → `generate_dialogue` (next scene) or `END` (all done)

- **`orchestrate_episode_duration()`**: Convenience function wrapping the agent

### 2. Updated `app/services/duration_orchestrator/__init__.py`

Added exports for new agent:

- `DurationOrchestratorAgent`
- `orchestrate_episode_duration`

### 3. Created `tests/unit/services/duration_orchestrator/test_agent.py`

Comprehensive tests for StateGraph and orchestration (12 tests):

- **`TestDurationOrchestratorAgent`** (5 tests):

  - `test_orchestrate_returns_result`: Verify result structure
  - `test_orchestrate_no_script_agent`: Error handling without script agent
  - `test_orchestrate_empty_scenes`: Error handling for empty scenes
  - `test_orchestrate_with_generation_config`: Config passthrough
  - `test_orchestrate_statistics_structure`: Verify statistics output

- **`TestOrchestrateEpisodeDuration`** (1 test):

  - `test_convenience_function`: Test helper function

- **`TestAgentBuildGraph`** (2 tests):

  - `test_build_graph_structure`: Verify all nodes present
  - `test_build_graph_entry_point`: Verify graph compiles

- **`TestSceneLoopIntegration`** (4 tests):
  - `test_multi_scene_orchestration`: Multi-scene flow
  - `test_budget_allocation_accuracy`: Budget distribution
  - `test_reasoning_log_populated`: Audit trail
  - `test_error_handling_in_loop`: Error recovery

## Validation

All 83 unit tests passed:

```
tests/unit/services/duration_orchestrator/test_budget_allocation.py: 26 passed
tests/unit/services/duration_orchestrator/test_generate_dialogue.py: 12 passed
tests/unit/services/duration_orchestrator/test_tts_trial.py: 12 passed
tests/unit/services/duration_orchestrator/test_commit_scene.py: 12 passed
tests/unit/services/duration_orchestrator/test_prepare_retry.py: 9 passed
tests/unit/services/duration_orchestrator/test_agent.py: 12 passed
```

Import verification:

```python
from app.services.duration_orchestrator import (
    DurationOrchestratorAgent,
    orchestrate_episode_duration,
)  # OK
```

## Next Steps

1. **Phase 5**: Episode Assembly and Final Validation

   - Implement `assemble_episode` node - merge all scenes' SceneBeat + Audio Timeline + storyboard
   - Implement `final_validation` node - verify total duration within ±10%

2. **Phase 6**: API Endpoints

   - Create `/api/v1/episodes/{id}/generate-with-duration-control` endpoint
   - Integrate with existing episode generation flow

3. **Phase 7**: Monitoring and Observability
   - Add structured logging for each node transition
   - Track retry counts and duration deviations

## Linked Commits

(To be added after git commit)
