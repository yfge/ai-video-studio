---
id: 2025-12-18T16-15-00Z-phase0-task012-centralized-exceptions
date: 2025-12-18T16:15:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [refactor, backend, phase0, exceptions]
related_paths:
  - ai-pic-backend/app/core/exceptions.py
  - ai-pic-backend/tests/unit/core/test_exceptions.py
summary: "Phase 0 Task 0.1.2: Created centralized exception hierarchy to replace 246 scattered HTTPException raises"
---

## User Prompt

User initiated refactoring plan execution with "开始". Starting with Phase 0, Task 0.1.2: Create centralized exception classes (core/exceptions.py) - the easiest foundation task with no dependencies.

## Goals

1. Create comprehensive domain exception hierarchy to replace scattered HTTPException raises
2. Provide structured error responses with error codes and context
3. Include factory methods for common resource types
4. Write comprehensive test coverage (31 test cases)
5. Establish foundation for exception middleware (Task 0.1.3)

## Changes

### Created app/core/exceptions.py (~280 lines)

**Exception Hierarchy:**

```
DomainError (base class)
├── NotFoundError (404)
│   ├── Factory methods: user(), virtual_ip(), script(), episode(), story(), scene(), shot(), beat(), environment(), image()
├── ValidationError (400)
│   ├── MissingFieldError
│   ├── InvalidFormatError
│   └── DuplicateError
├── UnauthorizedError (401)
├── ForbiddenError (403)
├── ConflictError (409)
├── ServiceError (500)
│   ├── GenerationFailedError
│   │   ├── Factory methods: image(), video(), script(), story(), audio()
│   └── ConfigurationError
└── ExternalServiceError (503)
```

**Key Features:**

1. **Structured Error Responses:**

   - `status_code`: HTTP status code
   - `error_code`: Machine-readable error code
   - `message`: Human-readable message
   - `context`: Additional debugging context
   - `to_dict()`: JSON serialization method

2. **Convenience Factory Methods:**

   ```python
   # Before (scattered throughout code):
   raise HTTPException(status_code=404, detail="用户不存在")

   # After (domain exception):
   raise NotFoundError.user(user_id)
   ```

3. **Context Enrichment:**
   ```python
   raise GenerationFailedError(
       "图像",
       "API超时",
       context={"provider": "openai", "attempt": 3}
   )
   ```

**Exception Usage Patterns:**

- **NotFoundError**: 404 errors (replaces 64 HTTPException instances)
- **ValidationError**: 400 errors (replaces 53 instances)
- **ServiceError**: 500 errors (replaces 61 instances)
- **ExternalServiceError**: 503 errors (replaces 11 instances)

Total: Replaces 246 HTTPException raises identified in codebase analysis.

### Created tests/unit/core/test_exceptions.py (~217 lines)

**Test Coverage: 31 test cases across 5 test classes**

1. **TestDomainError** (4 tests): Base exception functionality
2. **TestNotFoundError** (6 tests): Resource not found patterns
3. **TestValidationError** (7 tests): Validation error subclasses
4. **TestAuthErrors** (3 tests): Auth/permission errors
5. **TestServiceErrors** (8 tests): Server-side errors
6. **TestExceptionToDict** (3 tests): JSON serialization

**All tests passing:** ✅ 31 passed, 0 failed

## Validation

### Test Results

```bash
pytest tests/unit/core/test_exceptions.py -v
# 31 passed, 29 warnings in 0.07s
```

### Code Quality Checks

✅ **File Size Compliance:**

- `exceptions.py`: 280 lines (✅ < 300 line limit)
- `test_exceptions.py`: 217 lines (✅ < 300 line limit)

✅ **Single Responsibility:**

- One file, one purpose: Domain exception hierarchy
- Clear separation of exception types

✅ **No Duplication:**

- Base class provides common functionality
- Factory methods eliminate repetitive exception creation

✅ **Testing:**

- Comprehensive test coverage for all exception types
- Edge cases tested (with/without IDs, custom messages, context)

✅ **Documentation:**

- Docstrings with usage examples for all classes
- Module-level documentation explaining purpose and usage

## Impact

**Problem Solved:**

- Current codebase has 246 scattered `HTTPException` raises
- No consistency in error messages or status codes
- No machine-readable error codes
- No structured context for debugging

**Foundation Established:**

- Domain exceptions ready to use in all endpoints/services
- Enables Task 0.1.3 (exception middleware)
- Enables gradual migration from HTTPException to domain exceptions

**Next Steps:**

1. Task 0.1.3: Create exception middleware to convert domain exceptions → HTTP responses
2. Begin gradual migration: Replace HTTPException with domain exceptions (can start immediately in new code)

## Next Steps

1. ✅ Commit this task with ledger entry
2. 🔄 Continue to Task 0.1.3: Create exception middleware
3. Future: Begin migrating existing HTTPException raises (can happen incrementally)

## Linked Commits

- ee045fa refactor(backend): create centralized exception hierarchy [phase0]
