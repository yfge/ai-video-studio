---
id: 2025-12-26T12-30-00Z-duration-orchestrator-phase6-api-integration
date: 2025-12-26T12:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, duration-orchestrator, api-integration, dialogue-audio]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/services/duration_controlled_dialogue_service.py
summary: "Duration Orchestrator Phase 6: Integrated into existing dialogue-audio API with use_duration_control parameter"
---

## User Prompt

Continue with Phase 6 of Duration Orchestrator - API Integration. User confirmed to integrate into existing API rather than creating a new endpoint.

## Goals

1. Add `use_duration_control` parameter to existing `dialogue-audio/generate-async` API
2. Create integration service for Duration Orchestrator
3. Modify task processor to branch based on `use_duration_control` flag

## Changes

### 1. Updated `app/api/v1/endpoints/scripts_legacy.py`

Added `use_duration_control` parameter to `ScriptDialogueAudioGenerateRequest`:

```python
class ScriptDialogueAudioGenerateRequest(BaseModel):
    # ... existing fields ...
    use_duration_control: bool = Field(
        False,
        description="是否启用时长精控（Duration Orchestrator Agent）",
    )
```

Modified `_process_script_dialogue_audio_task` to branch on `use_duration_control`:
- When `True`: Calls `generate_dialogue_with_duration_control()` from new service
- When `False`: Uses traditional scene-by-scene generation (existing behavior)

### 2. Created `app/services/duration_controlled_dialogue_service.py`

New service module for duration-controlled dialogue generation:

- **`_scene_to_dict()`**: Converts Scene ORM to dict for orchestrator
- **`_episode_to_dict()`**: Converts Episode ORM to dict
- **`_story_to_dict()`**: Converts Story ORM to dict
- **`generate_dialogue_with_duration_control()`**: Main entry point
  - Converts ORM objects to orchestrator-compatible format
  - Creates DurationOrchestratorAgent instance
  - Executes orchestration
  - Returns result with success, statistics, validation
- **`persist_orchestrator_results()`**: Placeholder for DB persistence (TODO)

### 3. Updated `tasks.md`

- Updated Phase 6 tasks to reflect new approach (existing API integration)
- Marked Phase 6.1, 6.2, 6.3 as completed
- Updated "下一步" section

## Validation

All 108 unit tests passing:

```
python -m pytest tests/unit/services/duration_orchestrator/ -v
# 108 passed
```

Import verification:
```python
from app.services.duration_controlled_dialogue_service import (
    generate_dialogue_with_duration_control,
)  # OK

from app.api.v1.endpoints.scripts_legacy import (
    generate_script_dialogue_audio_async,
)  # OK
```

## Next Steps

1. **Phase 6.4**: Implement result persistence
   - Update Scene `estimated_duration_seconds` with actual values
   - Create/update SceneBeat records from orchestrator output
   - Update Script dialogue timeline data

2. **Phase 6.5**: Write API integration tests
   - Test with `use_duration_control=false` (existing behavior)
   - Test with `use_duration_control=true` (orchestrator path)

3. **Phase 7**: Monitoring and Observability
   - Add structured logging for orchestrator flow
   - Add progress callbacks

## Linked Commits

- `cc7c158` feat(duration-orchestrator): integrate into dialogue-audio API
