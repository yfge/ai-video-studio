---
id: 2025-12-18T15-45-00Z-refine-agents-md-with-codebase-patterns
date: 2025-12-18T15:45:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [docs, architecture, standards, refactor, backend, frontend]
related_paths:
  - AGENTS.md
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "Refined AGENTS.md with specific backend and frontend architecture standards based on actual codebase violations"
---

## User Prompt

User requested comprehensive codebase review and refinement of AGENTS.md with specific, actionable guidance based on actual code patterns and violations discovered.

## Goals

1. Perform deep architectural analysis of entire codebase (backend + frontend)
2. Identify specific file size violations and anti-patterns
3. Add backend-specific architecture standards to AGENTS.md
4. Add frontend-specific architecture standards to AGENTS.md
5. Include concrete examples from actual codebase
6. Add code review checklist for agents
7. Make standards immediately actionable with clear patterns

## Changes

### Codebase Analysis (via Explore agent)

Comprehensive "very thorough" exploration revealed:

**Critical Backend Violations:**
- `scripts.py`: 4,168 lines (14x limit) - 68 functions handling scripts/episodes/storyboards/dialogue/video
- `ai_service.py`: 2,910 lines (God object)
- `episodes.py`: 1,605 lines
- `virtual_ip_images.py`: 1,364 lines
- `ai_service_manager.py`: 1,301 lines
- `dialogue_audio_service.py`: 1,261 lines
- `volcengine_provider.py`: 1,409 lines

**Critical Frontend Violations:**
- `storyboard/page.tsx`: 3,279 lines with 100+ state variables (13x limit)
- `api.ts`: 2,627 lines with 100+ interface definitions (10x limit)
- `episodes/[id]/page.tsx`: 1,580 lines
- `virtual-ip/[id]/images/page.tsx`: 1,143 lines

**Key Findings:**
- 212+ HTTPException raises with no centralized error handling
- DB queries scattered across endpoints (no repository pattern)
- 8 provider implementations with duplicated auth/retry/logging code
- 21 frontend components at root with no organization
- Only 3 custom hooks despite massive state management needs
- 0 frontend tests

### AGENTS.md Additions

Added three major sections (380+ lines of new guidance):

#### 1. Backend-Specific Architecture Standards

**API Endpoint Organization:**
- Listed actual violations with line counts
- Mandatory thin controller pattern (< 50 lines per route)
- Standard endpoint structure with dependency injection
- Refactoring priorities for existing monoliths

**Service Layer Organization:**
- Listed God object violations
- Service file limit: 250 lines (stricter than general 300)
- Repository pattern for data access with example structure
- Clear separation: business logic → services, data → repositories, external → providers

**Provider Pattern Consistency:**
- Listed all 8 providers
- Mandatory BaseProvider extension
- Shared error handling, retry logic, auth patterns, polling utilities
- Provider file limit: 400 lines (with justification)
- Code reuse targets (auth/logging/retry duplicated 8x)

**Database & Repository Pattern:**
- Noted 212+ direct SQLAlchemy calls
- Mandatory repository pattern for new code
- Repository interface example
- Services never touch SQLAlchemy directly

**Error Handling:**
- Noted 212 HTTPException instances
- Centralized exception classes in `core/exceptions.py`
- Exception middleware for domain → HTTP conversion
- No direct HTTPException in business logic

#### 2. Frontend-Specific Architecture Standards

**Page Component Size Limits:**
- Listed actual violations (3,279 line storyboard page!)
- Page component limit: 200 lines (stricter than 250 general)
- Container/presentation split pattern
- Concrete refactoring example for storyboard page

**Component Organization:**
- Noted 21 components at root
- Mandatory structure: `ui/`, `shared/`, `features/`, `layouts/`
- Clear rules for each directory (size limits, responsibilities)

**Custom Hooks:**
- Noted only 3 hooks exist
- Mandatory patterns for extraction
- List of common hooks to create (useApi, useAsyncTask, usePolling, useToast, useConfirm)
- Hook file limit: 200 lines

**API Client Organization:**
- Noted 2,627 line api.ts monolith
- Mandatory split: `client.ts`, `types/`, `endpoints/`
- Type definitions separate from API calls
- Domain-based file organization

**State Management:**
- Documented current pattern (100+ useState)
- Standards for different state types
- Decision matrix: when to use useState vs Context vs React Query
- Props drilling limit

**Modal Component Pattern:**
- Noted 5 similar modals with duplication
- Mandatory base Modal component pattern
- Consistent modal API

#### 3. Additional Sections

**Testing Standards:**
- Backend: Test structure mirrors source, pytest markers, 80% coverage
- Frontend: TODO - setup testing library, 70% coverage target

**Documentation Standards:**
- API: OpenAPI/Swagger generation, docstring examples
- Component: JSDoc, future Storybook
- Architecture: ADR in `docs/adr/`

**Code Review Checklist:**
- Size compliance (5 specific checks)
- Structure compliance (4 checks)
- Testing compliance (3 checks)
- Documentation compliance (3 checks)
- Ledger compliance (4 checks)
- **Critical**: If ANY item fails, do NOT mark complete

## Validation

1. ✅ Explore agent completed comprehensive codebase analysis
2. ✅ All critical violations documented with specific file names and line counts
3. ✅ Backend standards added with concrete patterns and examples
4. ✅ Frontend standards added with refactoring examples
5. ✅ Code review checklist added for future enforcement
6. ✅ Standards are specific to this project (not generic advice)
7. ✅ File size: AGENTS.md now 479 lines (was 141 lines, +338 lines of actionable guidance)
8. ✅ All examples use actual file names from codebase
9. ✅ Standards reference real metrics from ai-shifu comparison

No code changes, documentation only.

## Next Steps

1. **Immediate**: Commit refined AGENTS.md with this ledger entry
2. **Future development**: All new code must follow these standards strictly
3. **Refactoring work**: Create separate tickets for addressing existing violations:
   - Backend: Split scripts.py into 8-10 focused files
   - Backend: Split ai_service.py by domain
   - Frontend: Refactor storyboard page with hooks + components
   - Frontend: Split api.ts into client + types + endpoints
   - Both: Extract duplicated patterns to shared utilities
4. **Tooling**: Implement pre-commit hooks to enforce file size limits automatically
5. **Agent compliance**: From now on, agents must use code review checklist before marking work complete

## Linked Commits

- 054e510 docs(agents): add comprehensive backend/frontend standards
