---
id: 2025-12-18T16-00-00Z-create-comprehensive-refactoring-plan
date: 2025-12-18T16:00:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [docs, refactor, planning, architecture]
related_paths:
  - docs/REFACTORING_PLAN.md
  - AGENTS.md
summary: "Created comprehensive 6-phase refactoring plan with 45+ tasks to address critical code quality violations"
---

## User Prompt

User requested a detailed refactoring plan based on the code quality violations discovered during codebase analysis.

## Goals

1. Create actionable refactoring plan based on actual violations
2. Organize tasks by priority and dependencies
3. Define clear phases with incremental approach
4. Specify acceptance criteria and target metrics
5. Provide execution strategy and risk mitigation
6. Make plan trackable and measurable

## Changes

### Created docs/REFACTORING_PLAN.md

Comprehensive refactoring plan with **6 phases** and **45+ tasks** organized by priority:

#### Phase 0: Foundation (8 tasks - CRITICAL)
Infrastructure that enables other refactorings:

**Backend Infrastructure (4 tasks):**
- Repository pattern base classes
- Centralized exception hierarchy (replace 212 HTTPException instances)
- Exception middleware for domain → HTTP conversion
- Shared provider utilities (retry, polling, auth) to eliminate duplication across 8 providers

**Frontend Infrastructure (4 tasks):**
- Base Modal component (replace 5 duplicated implementations)
- Foundation hooks (useModal, useAsyncTask, useApi)
- API client split phase 1 (extract HTTP client from 2,627-line api.ts)
- Component directory structure (organize 21 scattered components)

#### Phase 1: Critical Monoliths (12 tasks - HIGH)
Attack the most severe violations:

**Backend: scripts.py (4,168 lines → 8-10 files)**
- Create ScriptRepository, ScriptService, ScriptGenerator
- Split endpoints: crud.py, generation.py, episodes.py, storyboard.py
- Each file < 300 lines, each route < 50 lines
- 9 detailed tasks with dependencies

**Frontend: storyboard/page.tsx (3,279 lines → 10+ files)**
- Create StoryboardContext for state management
- Extract hooks: useStoryboard, useStoryboardTimeline
- Extract components: Timeline, FrameGrid, VideoGenerationModal
- Refactor page to < 200 lines (composition only)
- 7 detailed tasks with dependencies

#### Phase 2: Service Layer & God Objects (10 tasks - HIGH)

**Backend: ai_service.py (2,910 lines → 5-6 services)**
- Split by domain: ImageGenerationService, VideoGenerationService, TextGenerationService
- Refactor to thin coordinator pattern
- Each service < 300 lines

**Backend: Other large services**
- dialogue_audio_service.py (1,261 lines → 3 files)
- voice_catalog.py (1,171 lines → 3 files)

**Frontend: api.ts (2,627 lines → 15+ files)**
- Split types by domain (8 type files, ~200 lines each)
- Split endpoints by domain (8 endpoint files, ~250 lines each)
- Maintain backward compatibility during transition

#### Phase 3: Endpoint Refactoring (8 tasks - MEDIUM)
Apply thin controller pattern to remaining large endpoints:
- episodes.py (1,605 lines → 4-5 files)
- virtual_ip_images.py (1,364 lines → 3-4 files)
- story_structure.py (1,318 lines → 3-4 files)

#### Phase 4: Provider Consistency (9 tasks - MEDIUM)
Eliminate duplication across 8 AI providers:
- Refactor all providers to use shared utilities from Phase 0
- Target: ~400 lines per provider (down from 774-1,409)
- Consistent error handling, retry, logging, polling patterns

#### Phase 5: Page Component Refactoring (6 tasks - MEDIUM)
Apply container/presentation split to remaining large pages:
- episodes/[id]/page.tsx (1,580 lines)
- virtual-ip/[id]/images/page.tsx (1,143 lines)
- scripts/[id]/page.tsx (705 lines)
- 3 more pages (600-700 lines each)
- All target: < 200 lines

#### Phase 6: Testing & Documentation (Ongoing)
- Continuous testing during all phases
- OpenAPI documentation generation
- Component storybook (future)
- Architecture Decision Records (ADRs)

### Key Features of the Plan

**Incremental Approach:**
- Complete Phase 0 entirely before Phase 1
- Each task is atomic with clear acceptance criteria
- Each task = separate PR + ledger entry
- No "big bang" refactoring

**Dependency Management:**
- Tasks explicitly list dependencies
- Phase 0 has no dependencies (foundation)
- Later phases depend on Phase 0 utilities

**Risk Mitigation:**
- High-risk areas identified (scripts.py, storyboard page, api.ts)
- Mitigation strategies: extensive tests, feature flags, backward compatibility
- Rollback strategy: keep old code during transition

**Success Metrics:**

Quantitative:
- No Python file > 300 lines (currently 10+ violations)
- No TypeScript file > 250 lines (currently 6+ violations)
- Backend avg: 150-250 lines/file (currently ~380)
- Frontend avg: 100-200 lines/file (currently ~435)
- Test coverage: 80% backend, 70% frontend

Qualitative:
- Clear separation of concerns (API → Service → Repository → Model)
- Consistent patterns across all providers
- No code duplication (< 3 occurrences)
- Thin controllers, container/presentation split

**Quick Start Guide:**
Phase 0 tasks listed in execution order (1-8) for immediate action.

### Documentation Structure

**10 main sections:**
1. Executive Summary
2. Refactoring Phases (detailed breakdown)
3. Execution Strategy
4. Success Metrics
5. Risk Mitigation
6. Phase 0 Quick Start
7. Appendix: Complete task list by file

**2 comprehensive tables:**
- Backend files requiring refactoring (11 files, priority order)
- Frontend files requiring refactoring (8 files, priority order)

**Statistics:**
- Total tasks: 45+
- Total files to create/refactor: 100+
- Estimated line reduction: ~15,000 lines through better organization
- New shared utilities: ~2,000 lines

## Validation

1. ✅ Plan created based on actual codebase violations discovered by Explore agent
2. ✅ All critical violations (4,168 line files, 3,279 line files) addressed
3. ✅ Phases organized by priority and dependencies
4. ✅ Each task has clear acceptance criteria
5. ✅ Success metrics align with AGENTS.md standards
6. ✅ Incremental approach prevents big-bang risk
7. ✅ Backward compatibility strategy defined
8. ✅ Quick start guide for immediate action
9. ✅ Plan is trackable (45+ discrete tasks)
10. ✅ Plan is measurable (quantitative metrics)

No code changes, planning document only.

## Next Steps

1. **Immediate**: Commit refactoring plan with this ledger entry
2. **User decision**: Review and approve plan, prioritize phases
3. **Execution**: Begin Phase 0 tasks in order (foundation first)
4. **Tracking**: Create issues/tickets for each task
5. **Progress monitoring**: Update plan status as tasks complete
6. **Iteration**: Adjust plan based on discoveries during refactoring

**Recommended Start**: Phase 0 Task 0.1.2 (Create core/exceptions.py) - easiest, no dependencies, high impact

## Linked Commits

- 6d67069 docs(refactor): create comprehensive 6-phase refactoring plan
