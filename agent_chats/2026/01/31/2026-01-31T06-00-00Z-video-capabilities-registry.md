---
id: 2026-01-31T06-00-00Z-video-capabilities-registry
date: 2026-01-31T06:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, video, capabilities, duration]
related_paths:
  - ai-pic-backend/app/services/video/video_capabilities.py
  - ai-pic-backend/tests/unit/services/video/test_video_capabilities.py
  - ai-pic-backend/tasks.md
summary: "Implemented video capabilities registry for provider/model/resolution → allowed durations mapping with audit logging"
---

## User Prompt

Complete video-duration-alignment Phase 1: Create video capabilities parsing layer (provider/model/resolution → allowed durations/min/max) with audit logging.

## Goals

1. Create centralized video capabilities registry
2. Define allowed durations per provider/model/resolution
3. Provide auditable capability resolution with structured logging
4. Write comprehensive unit tests
5. Update tasks.md to mark the item complete

## Changes

### New Files Created

1. **`app/services/video/video_capabilities.py`** (300 lines) - Video capabilities registry:
   - `VideoCapability` dataclass for capability specifications
   - `CapabilityMatch` dataclass for resolution results with audit info
   - Provider-specific capabilities:
     - Google Veo: veo-3.1 (4/6/8s, 8s only at 1080p), veo-3.0 (8s), veo-2.0 (5/6/8s)
     - Keling: (5/10s)
     - MiniMax: (6/10s)
     - Volcengine: (4/6/8s)
   - `find_capability()` - lookup matching capability
   - `get_allowed_durations()` - get durations with resolution constraints
   - `resolve_video_duration()` - main entry point with audit logging
   - `get_capability_summary()` - documentation/debugging helper

2. **`tests/unit/services/video/test_video_capabilities.py`** (180 lines) - Unit tests:
   - TestFindCapability (8 tests) - provider/model matching
   - TestGetAllowedDurations (4 tests) - resolution constraints
   - TestResolveVideoDuration (10 tests) - duration resolution with audit
   - TestGetCapabilitySummary (3 tests) - summary generation
   - TestEdgeCases (3 tests) - None/empty/whitespace handling

### Key Features

1. **Centralized Registry**: All provider duration constraints in one place
2. **Resolution-Aware**: Handles cases like Veo 3.1@1080p only supporting 8s
3. **Auditable**: Structured logging with `video_capability_resolved` event
4. **Capability Source Tracking**: Each resolution includes source identifier (e.g., "google/veo-3.1@1080p")
5. **Audit Notes**: Human-readable notes explaining the resolution decision

### Updated Files

- **`tasks.md`**: Marked Phase 1 video capabilities item as complete

## Validation

```bash
python -m pytest tests/unit/services/video/test_video_capabilities.py -v
# Result: 27 passed tests
```

All 27 unit tests pass covering:
- Provider/model capability lookup
- Case-insensitive matching
- Resolution-specific constraints
- Duration ceiling logic
- Audit note generation
- Edge cases (None, empty, whitespace)

## Next Steps

1. Integrate `resolve_video_duration()` into existing video task submission flow to replace scattered hardcoded durations
2. Update provider modules (Google, Keling, MiniMax) to use centralized registry
3. Add API endpoint to expose capability summary for frontend validation

## Linked Commits

(To be committed)
