---
id: 2025-12-19T17-45-00Z-scripts-router-registration
date: 2025-12-19T17:45:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, refactor, api-endpoints, phase1]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
summary: "Update router registration for scripts package [Phase 1 Task 1.1.8]"
---

## User Prompt

Continue with refactoring plan Phase 1, Task 1.1.8: Update Router Registration.

## Goals

1. Rename old scripts.py to scripts_legacy.py for backward compatibility
2. Update scripts package to re-export legacy router
3. Maintain all API functionality during refactoring
4. Set up structure for gradual migration

## Changes

### Renamed Files

1. `scripts.py` → `scripts_legacy.py`
   - Preserves all storyboard and other unmigrated endpoints
   - Temporary solution during refactoring

### Modified Files

1. `ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py`
   - Import and re-export legacy router
   - Added comments explaining migration strategy
   - New CRUD/generation routers commented out (for future use)

## Strategy

The refactoring follows a phased approach:
1. Phase 1: Create new services and routers (completed)
2. Phase 2: Gradually migrate endpoints from legacy to new routers
3. Phase 3: Remove legacy file once all endpoints migrated

This ensures:
- Zero downtime during refactoring
- All existing functionality preserved
- Clear migration path for remaining endpoints

## Validation

```bash
# Import test - should have all routes
python -c "from app.api.v1.api import api_router; print('Routes:', len(api_router.routes))"
# Output: Routes: 194

# Verify legacy router accessible
python -c "from app.api.v1.endpoints.scripts_legacy import router; print('Legacy OK')"
# Output: Legacy OK
```

## Next Steps

1. Run build_prod_images.sh to verify everything works
2. Test in browser via Chrome MCP
3. Continue with Phase 1.2 (storyboard refactoring)

## Linked Commits

- Pending: This entry will be committed with the router changes
