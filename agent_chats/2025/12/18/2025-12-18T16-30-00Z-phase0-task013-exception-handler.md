---
id: 2025-12-18T16-30-00Z-phase0-task013-exception-handler
date: 2025-12-18T16:30:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [refactor, backend, phase0, exceptions, middleware]
related_paths:
  - ai-pic-backend/app/core/middleware.py
  - ai-pic-backend/app/main.py
  - ai-pic-backend/tests/unit/core/test_middleware.py
summary: "Phase 0 Task 0.1.3: Created exception handler to convert domain exceptions to HTTP responses"
---

## User Prompt

Continuing Phase 0 refactoring, implementing Task 0.1.3: Create exception middleware to convert DomainError exceptions to structured HTTP JSON responses.

## Goals

1. Create exception handler to catch DomainError and convert to HTTP responses
2. Integrate handler into FastAPI application
3. Log all domain errors with structured context
4. Write comprehensive test coverage (11 test cases)
5. Enable clean separation: business logic → domain exceptions → HTTP

## Changes

### Extended app/core/middleware.py (~40 lines added)

Created `domain_exception_handler()` function:

**Features:**
- Catches all DomainError exceptions app-wide
- Converts to structured JSON responses via `exc.to_dict()`
- Logs with structured context (error_code, path, method, etc.)
- Preserves HTTP status codes from domain exceptions

**Implementation approach:**
- Used FastAPI's `add_exception_handler()` instead of middleware
- More targeted than BaseHTTPMiddleware (only handles DomainError)
- Better performance (no wrapping all requests)
- Cleaner separation of concerns

**Logging:**
```python
logger.warning(
    f"Domain error occurred: {exc.error_code} - {exc.message}",
    extra={
        "error_code": exc.error_code,
        "error_message": exc.message,
        "error_context": exc.context,
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method,
    },
)
```

Note: Used `error_message` instead of `message` in `extra` to avoid conflict with logging's built-in `message` field.

### Updated app/main.py

Registered exception handler in `create_app()`:
```python
from app.core.middleware import domain_exception_handler
from app.core.exceptions import DomainError

# Exception handlers (must be registered before middlewares)
app.add_exception_handler(DomainError, domain_exception_handler)
```

**Important:** Exception handlers must be registered *before* middlewares for proper execution order.

### Created tests/unit/core/test_middleware.py (~179 lines)

**Test Coverage: 11 test cases across 3 test classes**

1. **TestDomainExceptionMiddleware** (6 tests):
   - NotFoundError → 404 conversion
   - ValidationError → 400 conversion
   - GenerationFailedError → 500 conversion
   - ExternalServiceError → 503 conversion
   - Context preservation in responses
   - Successful requests pass through

2. **TestMiddlewareIntegration** (4 tests):
   - Exception handler registration verification
   - Multiple sequential errors
   - JSON response format validation
   - Content-type header verification

3. **TestErrorLogging** (1 test):
   - Domain errors logged with structured context

**All tests passing:** ✅ 11 passed, 0 failed

## Validation

### Test Results
```bash
pytest tests/unit/core/test_middleware.py -v
# 11 passed, 29 warnings in 0.06s
```

### Code Quality Checks

✅ **File Size Compliance:**
- `middleware.py`: Total ~200 lines (✅ < 300 line limit)
- Added code: ~40 lines (handler function)
- `test_middleware.py`: 179 lines (✅ < 300 line limit)

✅ **Single Responsibility:**
- Handler has one job: convert DomainError → HTTP response
- Clean separation from other middleware

✅ **Integration:**
- Registered in main.py
- Works with all DomainError subclasses
- Does not interfere with other exception types

✅ **Testing:**
- Comprehensive coverage of all exception types
- Edge cases tested (context preservation, multiple errors)
- Logging verified

✅ **Documentation:**
- Docstrings with clear usage examples
- Comments explain design decisions

## Impact

**Problem Solved:**
- Endpoints can now raise domain exceptions without knowing about HTTP
- Clean separation: business logic uses domain vocabulary, not HTTP status codes
- Consistent error response format across entire API

**Enables:**
- Business logic can focus on domain concepts
- Easier testing (test domain logic without HTTP concerns)
- Gradual migration from HTTPException to domain exceptions
- Foundation for next tasks (repository pattern, service layer)

**Example Usage** (for future endpoints):
```python
# Old way (couples business logic to HTTP):
@router.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user

# New way (domain exceptions):
@router.get("/users/{user_id}")
async def get_user(user_id: int, service: UserService = Depends()):
    user = await service.get_user(user_id)
    # Service raises NotFoundError.user(user_id) if not found
    # Handler automatically converts to HTTP 404
    return user
```

## Next Steps

1. ✅ Commit this task with ledger entry
2. 🔄 Continue to Task 0.1.1: Create repository base classes
3. Future: Begin gradual migration of HTTPException → domain exceptions in endpoints

## Linked Commits

- 8057ecc refactor(backend): add domain exception handler [phase0]
