---
id: 2025-12-19T17-30-00Z-scripts-generation-endpoints
date: 2025-12-19T17:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, refactor, api-endpoints, phase1]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/generation.py
summary: "Split scripts.py generation endpoints [Phase 1 Task 1.1.5]"
---

## User Prompt

Continue with refactoring plan Phase 1, Task 1.1.5: Split scripts.py Endpoints - Generation.

## Goals

1. Create generation.py with AI script generation routes
2. Use ScriptGenerator for generation logic
3. Keep routes under 50 lines each
4. Maintain API compatibility

## Changes

### New Files

1. `ai-pic-backend/app/api/v1/endpoints/scripts/generation.py` (~108 lines)
   - Generation endpoints using ScriptGenerator:
     - `POST /generate` - Synchronous script generation
     - `POST /generate-async` - Async script generation via Celery
     - `POST /prompt/preview` - Preview generation prompt

### Modified Files

1. `ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py`
   - Added import for generation router
   - Included generation router in main router

## Validation

```bash
# Import test
python -c "from app.api.v1.endpoints.scripts import router; print('Import successful')"
# Output: Import successful

# Line count (under 300 limit)
wc -l generation.py
# Output: 108 lines
```

## Next Steps

1. Task 1.1.6: Split episode-related endpoints
2. Task 1.1.7: Split storyboard endpoints
3. Continue with remaining Phase 1 tasks

## Linked Commits

- Pending: This entry will be committed with the generation endpoints
