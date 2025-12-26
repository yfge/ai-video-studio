---
id: 2025-12-26T08-04-40Z-duration-orchestrator-phase3
date: 2025-12-26T08:04:40Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, duration-orchestrator, tts, langgraph]
related_paths:
  - ai-pic-backend/app/services/duration_orchestrator/nodes/tts_trial.py
  - ai-pic-backend/app/services/duration_orchestrator/nodes/commit_scene.py
  - ai-pic-backend/app/services/duration_orchestrator/nodes/prepare_retry.py
  - ai-pic-backend/app/services/duration_orchestrator/nodes/__init__.py
  - ai-pic-backend/tests/unit/services/duration_orchestrator/test_tts_trial.py
  - ai-pic-backend/tests/unit/services/duration_orchestrator/test_commit_scene.py
  - ai-pic-backend/tests/unit/services/duration_orchestrator/test_prepare_retry.py
summary: "Duration Orchestrator Phase 3: Implemented TTS trial, commit scene, and prepare retry nodes"
---

## User Prompt

Continue with Phase 3 of Duration Orchestrator - TTS estimation and validation nodes.

## Goals

1. Implement `tts_trial` node for duration estimation (both estimate and actual TTS modes)
2. Implement `commit_scene` node for finalizing scenes and triggering budget rebalance
3. Implement `prepare_retry` node for generating adjustment hints on validation failure
4. Write comprehensive unit tests for Phase 3 changes

## Changes

### 1. Created `app/services/duration_orchestrator/nodes/tts_trial.py`

TTS trial node with two modes:
- **Estimate mode** (default): Uses word count to estimate duration without calling TTS
  - `estimate_duration_from_dialogues()`: Calculates duration from character count
  - Uses `WORDS_PER_SECOND` (2.25 chars/s) constant
- **Actual TTS mode**: Calls TTS service with sampling strategy
  - Samples 3 dialogues (first, middle, last) for efficiency
  - Calculates actual speaking rate from samples
  - Extrapolates to total duration
  - Falls back to estimate mode if TTS fails

### 2. Created `app/services/duration_orchestrator/nodes/commit_scene.py`

Scene commit node:
- `commit_scene_node()`: Marks scene as COMMITTED
  - Saves committed scene data (dialogues, actual/target duration, deviation)
  - Triggers `rebalance_remaining_budgets()` if there's deviation and remaining scenes
  - Advances `current_scene_index` to next scene
- `should_continue_or_assemble()`: Router function
  - Returns "continue" if pending scenes remain
  - Returns "assemble" if all scenes processed

### 3. Created `app/services/duration_orchestrator/nodes/prepare_retry.py`

Retry preparation node:
- `prepare_retry_node()`: Prepares scene for regeneration
  - Generates adjustment hint using `compute_adjustment_hint()`
  - Sets `last_rejection_reason` ("duration_too_short" or "duration_too_long")
  - Clears generated dialogues for the scene
  - Forces COMMITTED status if `attempt_count >= MAX_RETRY_ATTEMPTS`
- `should_retry_or_fail()`: Router function
  - Returns "retry" if can retry
  - Returns "commit" if max retries reached or already committed

### 4. Updated `app/services/duration_orchestrator/nodes/__init__.py`

Exported all new nodes and routing functions:
- `tts_trial_node`, `estimate_duration_from_dialogues`
- `commit_scene_node`, `should_continue_or_assemble`
- `prepare_retry_node`, `should_retry_or_fail`

### 5. Created Test Files (33 new tests)

#### `test_tts_trial.py` (12 tests)
- `TestEstimateDurationFromDialogues`: 4 tests for duration calculation
- `TestTtsTrialNode`: 8 tests for node behavior

#### `test_commit_scene.py` (12 tests)
- `TestCommitSceneNode`: 9 tests for commit logic and rebalancing
- `TestShouldContinueOrAssemble`: 3 tests for routing

#### `test_prepare_retry.py` (9 tests)
- `TestPrepareRetryNode`: 6 tests for retry preparation
- `TestShouldRetryOrFail`: 3 tests for routing

## Validation

All 71 unit tests passed:

```
tests/unit/services/duration_orchestrator/test_budget_allocation.py: 26 passed
tests/unit/services/duration_orchestrator/test_generate_dialogue.py: 12 passed
tests/unit/services/duration_orchestrator/test_tts_trial.py: 12 passed
tests/unit/services/duration_orchestrator/test_commit_scene.py: 12 passed
tests/unit/services/duration_orchestrator/test_prepare_retry.py: 9 passed
```

Import verification:
```python
from app.services.duration_orchestrator.nodes import (
    tts_trial_node, commit_scene_node, prepare_retry_node
)  # OK
```

## Next Steps

1. **Phase 4**: Assemble LangGraph StateGraph
   - Create `agent.py` with complete StateGraph
   - Wire all nodes with conditional edges
   - Implement the main loop: generate → tts → validate → (commit|retry)

2. **Phase 5**: Episode assembly and final validation
   - Implement `assemble_episode` node
   - Implement `final_validation` node

## Linked Commits

(To be added after git commit)
