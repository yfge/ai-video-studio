---
id: 2025-12-19T16-45-00Z-script-service-phase1
date: 2025-12-19T16:45:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, refactor, service-layer, phase1]
related_paths:
  - ai-pic-backend/app/services/script/__init__.py
  - ai-pic-backend/app/services/script/script_service.py
  - ai-pic-backend/tests/unit/services/script/__init__.py
  - ai-pic-backend/tests/unit/services/script/test_script_service.py
summary: "Create ScriptService for CRUD business logic [Phase 1 Task 1.1.2]"
---

## User Prompt

Continue with refactoring plan Phase 1, Task 1.1.2: Create Script Service.

## Goals

1. Create ScriptService class with CRUD business logic
2. Use ScriptRepository for data access (from Task 1.1.1)
3. Implement user authorization checks
4. Add unit tests for all service methods
5. Keep service under 250 lines as per AGENTS.md standards

## Changes

### New Files

1. `ai-pic-backend/app/services/script/__init__.py` (~10 lines)
   - Package init with exports

2. `ai-pic-backend/app/services/script/script_service.py` (~230 lines)
   - `ScriptService` class with:
     - `get_script()`: Get by ID or business_id with authorization
     - `list_scripts()`: List with filters
     - `get_episode_scripts()`: Get scripts for episode
     - `create_script()`: Create with validation
     - `update_script()`: Update with authorization
     - `delete_script()`: Soft delete with authorization
   - `get_script_service()`: Factory function

3. `ai-pic-backend/tests/unit/services/script/test_script_service.py` (~180 lines)
   - 15 unit tests covering all methods
   - Tests for admin/regular user authorization
   - Tests for error cases (not found)

## Validation

```bash
# Import test
python -c "from app.services.script import ScriptService; print('Import successful')"
# Output: Import successful

# Unit tests
pytest tests/unit/services/script/test_script_service.py -v
# Output: 15 passed
```

## Next Steps

1. Task 1.1.3: Create Script Generation Service
2. Task 1.1.4: Split scripts.py CRUD endpoints to use ScriptService
3. Continue with remaining Phase 1 tasks

## Linked Commits

- Pending: This entry will be committed with the service implementation
