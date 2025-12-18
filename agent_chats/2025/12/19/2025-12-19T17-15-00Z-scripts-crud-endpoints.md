---
id: 2025-12-19T17-15-00Z-scripts-crud-endpoints
date: 2025-12-19T17:15:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, refactor, api-endpoints, phase1]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/crud.py
summary: "Split scripts.py CRUD endpoints to new module [Phase 1 Task 1.1.4]"
---

## User Prompt

Continue with refactoring plan Phase 1, Task 1.1.4: Split scripts.py Endpoints - CRUD.

## Goals

1. Create new scripts/ directory for endpoint modules
2. Create crud.py with basic CRUD routes
3. Use ScriptService for business logic (thin controller pattern)
4. Keep routes under 50 lines each
5. Maintain API compatibility

## Changes

### New Files

1. `ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py` (~15 lines)
   - Package init with router aggregation
   - Include sub-routers

2. `ai-pic-backend/app/api/v1/endpoints/scripts/crud.py` (~185 lines)
   - CRUD endpoints using ScriptService:
     - `GET /formats` - List supported formats
     - `GET /languages` - List supported languages
     - `POST /` - Create script
     - `GET /` - List scripts with filters
     - `GET /{script_id}` - Get script by ID
     - `GET /business/{business_id}` - Get by business ID
     - `PUT /{script_id}` - Update script
     - `PUT /business/{business_id}` - Update by business ID
     - `DELETE /{script_id}` - Delete script
     - `DELETE /business/{business_id}` - Delete by business ID
     - `GET /episode/{episode_id}` - Get episode scripts
     - `GET /episode/business/{business_id}` - Get by episode business ID

## Validation

```bash
# Import test
python -c "from app.api.v1.endpoints.scripts import router; print('Import successful')"
# Output: Import successful

# Line count (under 300 limit)
wc -l crud.py
# Output: 185 lines
```

## Next Steps

1. Task 1.1.5: Split scripts.py generation endpoints
2. Task 1.1.6: Split episode-related endpoints
3. Continue with remaining Phase 1 tasks

## Linked Commits

- Pending: This entry will be committed with the CRUD endpoints
