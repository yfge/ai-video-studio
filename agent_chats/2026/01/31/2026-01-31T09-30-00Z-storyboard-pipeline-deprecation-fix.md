---
id: 2026-01-31T09-30-00Z-storyboard-pipeline-deprecation-fix
date: 2026-01-31T09:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, storyboard, deprecation-fix, datetime]
related_paths:
  - ai-pic-backend/app/services/storyboard/pipeline/pipeline_state.py
  - ai-pic-backend/app/services/storyboard/pipeline/storyboard_pipeline.py
  - ai-pic-backend/app/services/storyboard/recovery/retry_strategy.py
  - ai-pic-backend/app/services/storyboard/sync/script_structure_sync.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/generation.py
summary: "Fixed datetime.utcnow() deprecation warnings in storyboard pipeline modules"
---

## User Prompt

Continue completing today's unfinished work from previous session.

## Goals

1. Review storyboard pipeline implementation status
2. Fix `datetime.utcnow()` deprecation warnings in storyboard modules
3. Verify all tests pass

## Changes

### 1. `app/services/storyboard/pipeline/pipeline_state.py`

- Added `timezone` import from datetime
- Added helper `_utcnow()` function returning timezone-aware UTC datetime
- Changed `ValidationResult.timestamp` default_factory from `datetime.utcnow` to `_utcnow`
- Changed `PipelineState.started_at` default_factory from `datetime.utcnow` to `_utcnow`
- Changed `record_recovery()` timestamp from `datetime.utcnow().isoformat()` to `datetime.now(timezone.utc).isoformat()`

### 2. `app/services/storyboard/pipeline/storyboard_pipeline.py`

- Added `timezone` import from datetime
- Replaced 3 occurrences of `datetime.utcnow()` with `datetime.now(timezone.utc)`

### 3. `app/services/storyboard/recovery/retry_strategy.py`

- Added `timezone` import from datetime
- Added helper `_utcnow()` function
- Changed `RetryContext.started_at` default_factory to `_utcnow`
- Replaced 4 occurrences of `datetime.utcnow()` with `datetime.now(timezone.utc)`

### 4. `app/services/storyboard/sync/script_structure_sync.py`

- Added `timezone` import from datetime
- Replaced `datetime.utcnow()` with `datetime.now(timezone.utc)`

### 5. `app/api/v1/endpoints/storyboard/generation.py`

- Added `timezone` import from datetime
- Replaced 2 occurrences of `datetime.utcnow()` with `datetime.now(timezone.utc)`

## Validation

### Unit Tests

```bash
python -m pytest tests/unit/services/storyboard/ -v --tb=short
# Result: 102 passed, 79 warnings (down from 368 warnings)

python -m pytest tests/unit/ -v --tb=short -q
# Result: 986 passed, 54 skipped, 537 warnings
```

All storyboard module tests pass. The warning count was reduced significantly by fixing
`datetime.utcnow()` deprecation in our code. Remaining warnings are from third-party
libraries (SQLAlchemy, factory) that we cannot control.

### Chrome E2E Verification

- URL: `http://localhost:8089/episodes/133/storyboard?scriptId=117`
- Account: geyunfei / Gyf@845261
- Results:
  - Storyboard management page loaded successfully
  - Episode 133 "雨夜代码与诗" with Script 117 (v1.0)
  - 5 scenes visible with proper navigation
  - Scene 1 shows 11 frames with timeline alignment (00:00.000–00:40.000)
  - All frames have generated keyframe images and Veo 3.1 videos
  - Audio timeline integration working (beats=68, version=2)
  - Frame-level data: start_ms/end_ms, duration, shot type, camera movement, composition
  - Reference images bound to frames (1-2 per frame)

## Next Steps

1. Continue with storyboard pipeline API integration testing
2. E2E validation with Chrome to verify the pipeline works end-to-end
3. Consider enabling `use_new_pipeline=True` by default after validation

## Linked Commits

(To be committed)
