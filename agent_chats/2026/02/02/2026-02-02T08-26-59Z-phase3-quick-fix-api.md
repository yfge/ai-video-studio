---
id: 2026-02-02T08-26-59Z-phase3-quick-fix-api
date: 2026-02-02T08:26:59Z
participants: [human, claude-opus-4-5]
models: [claude-opus-4-5-20251101]
tags: [backend, api, readiness-check, quick-fix, ai-generation]
related_paths:
  - ai-pic-backend/app/schemas/readiness.py
  - ai-pic-backend/app/services/readiness/__init__.py
  - ai-pic-backend/app/services/readiness/story_quick_fix.py
  - ai-pic-backend/app/api/v1/endpoints/stories/readiness.py
  - ai-pic-backend/tests/unit/services/readiness/test_story_quick_fix.py
  - ai-pic-backend/tests/integration/test_readiness_api.py
summary: "Implemented Phase 3 story quick-fix API for auto-fixing missing fields using AI"
---

## User Prompt

Continue implementing Phase 3 readiness check features - add the "一键补齐" (quick-fix) API that auto-fills missing story fields using AI generation.

## Goals

1. Create `StoryQuickFixService` to auto-fix missing story fields
2. Add `POST /stories/{story_id}/quick-fix` endpoint
3. Support dry_run mode to preview fixes without applying
4. Add comprehensive unit and integration tests

## Changes

### New Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `app/services/readiness/story_quick_fix.py` | ~190 | StoryQuickFixService with AI-powered field generation |
| `tests/unit/services/readiness/test_story_quick_fix.py` | ~210 | 14 unit tests for quick-fix service |

### Modified Files

| File | Change |
|------|--------|
| `app/schemas/readiness.py` | Added FixApplied, FixSkipped, QuickFixImprovement, QuickFixRequest, QuickFixResponse schemas |
| `app/services/readiness/__init__.py` | Export StoryQuickFixService |
| `app/api/v1/endpoints/stories/readiness.py` | Added quick-fix endpoint |
| `tests/integration/test_readiness_api.py` | Added 4 integration tests for quick-fix API |

### API Endpoints Added

```
POST /api/v1/stories/{story_id}/quick-fix
```

Request body:
```json
{
  "dry_run": false  // If true, only report what would be fixed
}
```

Response:
```json
{
  "story_id": 1,
  "dry_run": false,
  "fixes_applied": [
    {"check_name": "synopsis_present", "field": "synopsis", "old_value": null, "new_value": "..."}
  ],
  "fixes_skipped": [],
  "initial_readiness": {...},
  "final_readiness": {...},
  "improvement": {
    "initial_failed": 5,
    "final_failed": 2,
    "fixed_count": 3
  }
}
```

### Auto-Fixable Checks

| Check Name | Field | How it's Fixed |
|------------|-------|----------------|
| `synopsis_present` | synopsis | Generated from title/genre/premise using AI |
| `main_conflict_present` | main_conflict | Generated from synopsis/premise using AI |
| `setting_present` | setting_time | Generated from genre/synopsis or defaults to "当代" |
| `world_building_present` | world_building | Generated from genre/setting/synopsis using AI |

### Non-Fixable Checks (require manual action)

- `title_present` (CRITICAL) - Must be set manually
- `genre_present` (CRITICAL) - Must be set manually
- `has_characters` (CRITICAL) - Requires linking VirtualIP
- `main_characters_valid` (ERROR) - Requires valid VirtualIP references
- `virtual_ip_has_portrait` (ERROR) - Requires generating character images
- Marketing meta fields - Require user decision

## Validation

### Unit Tests
```bash
pytest tests/unit/services/readiness/test_story_quick_fix.py -v
# 14 passed
```

### All Readiness Tests
```bash
pytest tests/unit/services/readiness/ tests/integration/test_readiness_api.py -v
# 58 passed (27 story + 10 episode + 14 quick-fix unit + 7 integration)
```

### Linter
```bash
ruff check app/schemas/readiness.py app/services/readiness/ app/api/v1/endpoints/stories/readiness.py
# All checks passed!
```

## Next Steps

1. Frontend: Integrate quick-fix button in story generation UI
2. Frontend: Show readiness check results before episode generation
3. Chrome E2E: Validate complete flow (story missing fields → quick-fix → generate episode)

## Linked Commits

- de63e17 feat(backend): add story quick-fix API for auto-filling missing fields
