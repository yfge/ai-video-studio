---
id: 2026-02-02T07-22-26Z-phase3-readiness-check-api
date: 2026-02-02T07:22:26Z
participants: [human, claude-opus-4-5]
models: [claude-opus-4-5-20251101]
tags: [backend, api, readiness-check, generation]
related_paths:
  - ai-pic-backend/app/schemas/readiness.py
  - ai-pic-backend/app/services/readiness/__init__.py
  - ai-pic-backend/app/services/readiness/story_readiness.py
  - ai-pic-backend/app/services/readiness/episode_readiness.py
  - ai-pic-backend/app/api/v1/endpoints/stories/readiness.py
  - ai-pic-backend/app/api/v1/endpoints/stories/__init__.py
  - ai-pic-backend/tests/unit/services/readiness/__init__.py
  - ai-pic-backend/tests/unit/services/readiness/test_story_readiness.py
  - ai-pic-backend/tests/unit/services/readiness/test_episode_readiness.py
  - ai-pic-backend/tests/integration/test_readiness_api.py
summary: "Implemented Phase 3 Story/Episode readiness check API for pre-generation validation"
---

## User Prompt

Implement Phase 3 Readiness Check - a Story/Episode readiness check API that validates all prerequisites before generation. The system should check required fields, character linkages, marketing metadata, and content quality with CRITICAL/ERROR/WARNING/INFO severity levels.

## Goals

1. Create `ReadinessCheck` and `ReadinessResult` Pydantic schemas with severity levels
2. Implement `StoryReadinessChecker` service with checks for:
   - CRITICAL: title, genre, has_characters
   - ERROR: synopsis_present, main_characters_valid, virtual_ip_has_portrait
   - WARNING: marketing_meta (for short_drama), main_conflict, setting
   - INFO: world_building, character_relationships validation
3. Implement `EpisodeReadinessChecker` that composes story checks and adds:
   - CRITICAL: episode_exists, story_matches
   - WARNING: previous_episodes_complete
4. Create API endpoints for story and episode readiness checks
5. Add comprehensive unit and integration tests

## Changes

### New Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `app/schemas/readiness.py` | 78 | ReadinessCheck/ReadinessResult Pydantic models with computed fields |
| `app/services/readiness/__init__.py` | 11 | Module exports for readiness services |
| `app/services/readiness/story_readiness.py` | 215 | StoryReadinessChecker with all story-level checks |
| `app/services/readiness/episode_readiness.py` | 143 | EpisodeReadinessChecker composing story checks |
| `app/api/v1/endpoints/stories/readiness.py` | 85 | Two API endpoints for readiness checks |
| `tests/unit/services/readiness/__init__.py` | 1 | Test module init |
| `tests/unit/services/readiness/test_story_readiness.py` | 193 | 17 unit tests for story readiness |
| `tests/unit/services/readiness/test_episode_readiness.py` | 182 | 10 unit tests for episode readiness |
| `tests/integration/test_readiness_api.py` | 218 | 13 integration tests for API endpoints |

### Modified Files

| File | Change |
|------|--------|
| `app/api/v1/endpoints/stories/__init__.py` | Added readiness router to story endpoints |

### API Endpoints Added

```
POST /api/v1/stories/{story_id}/readiness-check
POST /api/v1/stories/{story_id}/episodes/{episode_id}/readiness-check
```

Both endpoints return `ReadinessResult` with:
- `ready`: True if no CRITICAL/ERROR issues
- `can_proceed`: True if no CRITICAL issues
- `checks`: List of all check results with severity
- `summary`: Human-readable summary
- Computed fields: `critical_issues`, `errors`, `warnings`, `info_issues`, `failed_count`, `passed_count`

## Validation

### Unit Tests
```bash
pytest tests/unit/services/readiness/ -v
# 27 passed
```

### Integration Tests
```bash
pytest tests/integration/test_readiness_api.py -v
# 13 passed
```

### Linter
```bash
ruff check app/schemas/readiness.py app/services/readiness/ app/api/v1/endpoints/stories/readiness.py
# All checks passed!
```

## Next Steps

1. Add frontend UI to display readiness check results before generation
2. Integrate readiness check into generation workflow (pre-flight check)
3. Consider async version for batch validation of multiple stories
4. Add more granular checks as requirements emerge

## Linked Commits

- d80512e feat(backend): implement Phase 3 story/episode readiness check API
