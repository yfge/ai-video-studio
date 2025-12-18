# AI-Video-Studio Refactoring Plan

**Version**: 1.0
**Created**: 2025-12-18
**Status**: Planning
**Estimated Total Tasks**: 45+

## Executive Summary

Based on comprehensive codebase analysis, this project requires significant refactoring to meet the architecture standards defined in AGENTS.md. The current codebase shows classic signs of rapid AI-assisted development without intermediate refactoring:

**Critical Violations:**
- 10+ backend files exceed 300-line limit (largest: 4,168 lines)
- 6+ frontend files exceed 250-line limit (largest: 3,279 lines)
- God objects, duplicated code, no repository pattern, poor component organization

**Target Metrics** (align with ai-shifu):
- Backend: 186 lines/file average (currently ~380)
- Frontend: 119 lines/file average (currently ~435)
- Modular architecture with clear separation of concerns

---

## Refactoring Phases

### Phase 0: Foundation (Infrastructure)
**Goal**: Create shared utilities and patterns that other refactorings depend on
**Priority**: CRITICAL - Must complete before other phases
**Estimated Tasks**: 8

#### P0.1: Backend Infrastructure

**Task 0.1.1**: Create Repository Pattern Base Classes
- **File**: `ai-pic-backend/app/repositories/base.py`
- **Description**: Abstract base repository with CRUD operations
- **Acceptance Criteria**:
  - `BaseRepository` class with generic CRUD methods
  - Async support for all operations
  - Transaction context manager
  - Soft delete support integration
- **Impact**: Enables P1 endpoint refactoring
- **Size**: ~150 lines

**Task 0.1.2**: Create Centralized Exception Classes
- **File**: `ai-pic-backend/app/core/exceptions.py`
- **Description**: Domain exception hierarchy to replace 212 HTTPException instances
- **Acceptance Criteria**:
  - Base `DomainError` class
  - Specific exceptions: `NotFoundError`, `ValidationError`, `GenerationFailedError`, etc.
  - Exception→HTTP status code mapping
- **Impact**: Enables consistent error handling across all endpoints
- **Size**: ~200 lines

**Task 0.1.3**: Create Exception Middleware
- **File**: `ai-pic-backend/app/core/middleware.py` (extend existing)
- **Description**: Catch domain exceptions and convert to HTTP responses
- **Acceptance Criteria**:
  - Middleware catches all DomainError subclasses
  - Structured error response schema
  - Logging integration
- **Impact**: Enables removing HTTPException from business logic
- **Size**: ~100 lines

**Task 0.1.4**: Extract Shared Provider Utilities
- **Files**:
  - `ai-pic-backend/app/core/retry_utils.py`
  - `ai-pic-backend/app/core/polling_utils.py`
  - `ai-pic-backend/app/core/http_utils.py`
- **Description**: Shared utilities currently duplicated across 8 providers
- **Acceptance Criteria**:
  - `retry_with_backoff()` decorator (< 80 lines)
  - `poll_until_complete()` async utility (< 100 lines)
  - `build_auth_headers()`, `normalize_url()` helpers (< 70 lines)
- **Impact**: Enables provider refactoring, reduces 800+ lines of duplication
- **Size**: ~250 lines total

#### P0.2: Frontend Infrastructure

**Task 0.2.1**: Create Base Modal Component
- **File**: `ai-pic-frontend/src/components/ui/Modal.tsx`
- **Description**: Reusable modal base replacing 5 duplicated implementations
- **Acceptance Criteria**:
  - Props: `isOpen`, `onClose`, `title`, `children`, `footer`
  - Backdrop click to close
  - ESC key support
  - Accessible (ARIA labels)
- **Impact**: Enables modal component refactoring
- **Size**: ~100 lines

**Task 0.2.2**: Create Custom Hook Utilities
- **Files**:
  - `ai-pic-frontend/src/hooks/useModal.ts`
  - `ai-pic-frontend/src/hooks/useAsyncTask.ts`
  - `ai-pic-frontend/src/hooks/useApi.ts`
- **Description**: Foundation hooks for state management patterns
- **Acceptance Criteria**:
  - `useModal()`: open/close/data state management
  - `useAsyncTask()`: loading/error/data state with reset
  - `useApi()`: fetch wrapper with auth and error handling
- **Impact**: Enables page component refactoring
- **Size**: ~150 lines each (~450 total)

**Task 0.2.3**: Split API Client - Phase 1 (Types)
- **Files**:
  - `ai-pic-frontend/src/utils/api/client.ts` (HTTP client only)
  - `ai-pic-frontend/src/utils/api/types/index.ts` (re-export types)
- **Description**: Extract HTTP client from types (first step of api.ts split)
- **Acceptance Criteria**:
  - `client.ts`: fetch wrapper, auth token, error handling (< 150 lines)
  - Types remain in api.ts temporarily (will split in P2)
  - All existing code continues to work
- **Impact**: Enables gradual api.ts migration
- **Size**: ~150 lines (client)

**Task 0.2.4**: Create Component Directory Structure
- **Directories**:
  - `ai-pic-frontend/src/components/ui/`
  - `ai-pic-frontend/src/components/shared/`
  - `ai-pic-frontend/src/components/features/`
  - `ai-pic-frontend/src/components/layouts/`
- **Description**: Organize existing 21 components
- **Acceptance Criteria**:
  - Move `AdminLayout.tsx` → `layouts/`
  - Move shared modals to `shared/modals/`
  - Update all imports
  - No functionality changes
- **Impact**: Enables organized component refactoring
- **Size**: No new code, migration only

---

### Phase 1: Critical Monoliths (Highest Impact)
**Goal**: Break down the most severe violations
**Priority**: HIGH - Addresses 14x and 13x violations
**Estimated Tasks**: 12

#### P1.1: Backend - scripts.py (4,168 lines → 8-10 files)

**Current State**: 68 functions handling scripts, episodes, storyboards, dialogue, video generation

**Task 1.1.1**: Create Script Repository
- **File**: `ai-pic-backend/app/repositories/script_repository.py`
- **Description**: Encapsulate all script DB operations
- **Acceptance Criteria**:
  - CRUD operations for Script model
  - Query methods: `list_by_user()`, `list_by_virtual_ip()`, `search()`
  - Uses BaseRepository from P0.1.1
- **Size**: ~200 lines

**Task 1.1.2**: Create Script Service
- **File**: `ai-pic-backend/app/services/script/script_service.py`
- **Description**: Business logic for script CRUD (no generation)
- **Acceptance Criteria**:
  - Uses ScriptRepository for data access
  - Validation logic
  - No direct DB queries
- **Dependencies**: Task 1.1.1
- **Size**: ~250 lines

**Task 1.1.3**: Create Script Generation Service
- **File**: `ai-pic-backend/app/services/script/script_generator.py`
- **Description**: AI-powered script generation logic
- **Acceptance Criteria**:
  - Uses AIServiceManager for AI calls
  - Template processing
  - Error handling with domain exceptions
- **Dependencies**: P0.1.2 (exceptions)
- **Size**: ~300 lines

**Task 1.1.4**: Split scripts.py Endpoints - CRUD
- **File**: `ai-pic-backend/app/api/v1/endpoints/scripts/crud.py`
- **Description**: Basic CRUD routes only
- **Routes**: GET, POST, PUT, DELETE `/scripts/`
- **Acceptance Criteria**:
  - Each route < 50 lines
  - Uses ScriptService via dependency injection
  - No business logic in routes
- **Dependencies**: Task 1.1.2
- **Size**: ~250 lines (5-6 routes)

**Task 1.1.5**: Split scripts.py Endpoints - Generation
- **File**: `ai-pic-backend/app/api/v1/endpoints/scripts/generation.py`
- **Description**: Script generation routes
- **Routes**: POST `/scripts/generate`, `/scripts/regenerate`
- **Acceptance Criteria**:
  - Routes delegate to ScriptGenerator
  - Background task handling
  - Progress tracking
- **Dependencies**: Task 1.1.3
- **Size**: ~200 lines (3-4 routes)

**Task 1.1.6**: Split scripts.py Endpoints - Episode Related
- **File**: `ai-pic-backend/app/api/v1/endpoints/scripts/episodes.py`
- **Description**: Episode-related routes (should eventually move to episodes/)
- **Routes**: Episode generation from scripts
- **Acceptance Criteria**:
  - Extract episode logic from scripts.py
  - Mark for future migration to episodes/
- **Size**: ~300 lines

**Task 1.1.7**: Split scripts.py Endpoints - Storyboard
- **File**: `ai-pic-backend/app/api/v1/endpoints/scripts/storyboard.py`
- **Description**: Storyboard generation routes
- **Routes**: POST `/scripts/{id}/storyboard`
- **Dependencies**: Storyboard service (create if needed)
- **Size**: ~250 lines

**Task 1.1.8**: Update Router Registration
- **File**: `ai-pic-backend/app/api/v1/endpoints/__init__.py`
- **Description**: Register new script sub-routers
- **Acceptance Criteria**:
  - Include all new script routers
  - Remove old scripts.py import
  - Verify all routes still accessible
- **Size**: ~20 lines changed

**Task 1.1.9**: Migration & Cleanup
- **Description**: Remove original scripts.py, update tests
- **Acceptance Criteria**:
  - Delete `scripts.py`
  - Update all test imports
  - All tests passing
  - No regression in functionality

#### P1.2: Frontend - storyboard/page.tsx (3,279 lines → 10+ files)

**Current State**: 100+ state variables, all logic in one component

**Task 1.2.1**: Create Storyboard Context
- **File**: `ai-pic-frontend/src/contexts/StoryboardContext.tsx`
- **Description**: Centralized state management for storyboard feature
- **Acceptance Criteria**:
  - Context for frames, timeline, selection state
  - Actions: add/remove/update frames
  - No UI logic
- **Size**: ~200 lines

**Task 1.2.2**: Create useStoryboard Hook
- **File**: `ai-pic-frontend/src/hooks/useStoryboard.ts`
- **Description**: Main business logic hook
- **Acceptance Criteria**:
  - Frame management logic
  - Video generation coordination
  - Image selection logic
  - Uses StoryboardContext
- **Dependencies**: Task 1.2.1
- **Size**: ~250 lines

**Task 1.2.3**: Create useStoryboardTimeline Hook
- **File**: `ai-pic-frontend/src/hooks/useStoryboardTimeline.ts`
- **Description**: Timeline-specific logic
- **Acceptance Criteria**:
  - Playback controls
  - Frame navigation
  - Duration calculations
- **Size**: ~200 lines

**Task 1.2.4**: Extract Timeline Component
- **File**: `ai-pic-frontend/src/components/features/storyboard/Timeline.tsx`
- **Description**: Timeline UI component
- **Acceptance Criteria**:
  - Uses useStoryboardTimeline
  - Presentational only
  - < 200 lines
- **Dependencies**: Task 1.2.3
- **Size**: ~180 lines

**Task 1.2.5**: Extract Frame Grid Component
- **File**: `ai-pic-frontend/src/components/features/storyboard/FrameGrid.tsx`
- **Description**: Frame display and management UI
- **Acceptance Criteria**:
  - Frame cards display
  - Selection handling
  - Drag and drop (if applicable)
- **Size**: ~200 lines

**Task 1.2.6**: Extract Video Generation Modal
- **File**: `ai-pic-frontend/src/components/features/storyboard/VideoGenerationModal.tsx`
- **Description**: Video generation UI
- **Acceptance Criteria**:
  - Uses base Modal from P0.2.1
  - Form for video parameters
  - Progress display
- **Dependencies**: P0.2.1
- **Size**: ~180 lines

**Task 1.2.7**: Refactor Main Storyboard Page
- **File**: `ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`
- **Description**: Composition of extracted components
- **Acceptance Criteria**:
  - < 200 lines
  - Only layout and composition
  - No business logic
  - Uses StoryboardProvider
- **Dependencies**: All above tasks
- **Size**: ~150 lines (down from 3,279!)

---

### Phase 2: Service Layer & God Objects
**Goal**: Split monolithic services by domain
**Priority**: HIGH - Improves maintainability significantly
**Estimated Tasks**: 10

#### P2.1: Backend - ai_service.py (2,910 lines → 5-6 services)

**Task 2.1.1**: Create Image Generation Service
- **File**: `ai-pic-backend/app/services/image/image_generation_service.py`
- **Description**: Extract image generation logic
- **Size**: ~300 lines

**Task 2.1.2**: Create Video Generation Service
- **File**: `ai-pic-backend/app/services/video/video_generation_service.py`
- **Description**: Extract video generation logic
- **Size**: ~300 lines

**Task 2.1.3**: Create Text Generation Service
- **File**: `ai-pic-backend/app/services/text/text_generation_service.py`
- **Description**: Extract script/dialogue generation
- **Size**: ~250 lines

**Task 2.1.4**: Refactor AIService to Coordinator
- **File**: `ai-pic-backend/app/services/ai_coordinator.py`
- **Description**: Thin coordinator delegating to specialized services
- **Acceptance Criteria**:
  - < 200 lines
  - Only orchestration logic
  - Delegates to specialized services
- **Size**: ~180 lines

#### P2.2: Backend - Other Large Services

**Task 2.2.1**: Split dialogue_audio_service.py (1,261 lines)
- **Files**:
  - `services/audio/dialogue_service.py` (~300 lines)
  - `services/audio/audio_generator.py` (~300 lines)
  - `services/audio/timeline_processor.py` (~250 lines)

**Task 2.2.2**: Split voice_catalog.py (1,171 lines)
- **Files**:
  - `services/audio/voice_repository.py` (~200 lines)
  - `services/audio/voice_selector.py` (~250 lines)
  - `services/audio/voice_cache.py` (~150 lines)

#### P2.3: Frontend - api.ts (2,627 lines → 15+ files)

**Task 2.3.1**: Split Type Definitions by Domain
- **Files**:
  - `utils/api/types/script.types.ts` (~200 lines)
  - `utils/api/types/episode.types.ts` (~200 lines)
  - `utils/api/types/virtual-ip.types.ts` (~180 lines)
  - `utils/api/types/story.types.ts` (~180 lines)
  - `utils/api/types/image.types.ts` (~150 lines)
  - `utils/api/types/video.types.ts` (~150 lines)
  - `utils/api/types/user.types.ts` (~100 lines)
  - `utils/api/types/task.types.ts` (~100 lines)

**Task 2.3.2**: Split API Endpoints by Domain
- **Files**:
  - `utils/api/endpoints/scripts.ts` (~250 lines)
  - `utils/api/endpoints/episodes.ts` (~250 lines)
  - `utils/api/endpoints/virtual-ip.ts` (~200 lines)
  - `utils/api/endpoints/stories.ts` (~200 lines)
  - `utils/api/endpoints/images.ts` (~180 lines)
  - `utils/api/endpoints/videos.ts` (~150 lines)
  - `utils/api/endpoints/users.ts` (~150 lines)
  - `utils/api/endpoints/tasks.ts` (~100 lines)

**Task 2.3.3**: Create API Index with Re-exports
- **File**: `utils/api/index.ts`
- **Description**: Backward compatibility layer
- **Acceptance Criteria**:
  - Re-export all types and functions
  - Existing imports continue to work
  - Migration guide in comments

---

### Phase 3: Endpoint Refactoring (Remaining Large Files)
**Goal**: Apply thin controller pattern to remaining large endpoints
**Priority**: MEDIUM - Standardize architecture
**Estimated Tasks**: 8

**Task 3.1**: Refactor episodes.py (1,605 lines → 4-5 files)
- Create EpisodeRepository, EpisodeService, EpisodeGenerator
- Split routes: crud.py, generation.py, storyboard.py

**Task 3.2**: Refactor virtual_ip_images.py (1,364 lines → 3-4 files)
- Create ImageRepository, ImageService, ImageGenerator
- Split routes: crud.py, generation.py, selection.py

**Task 3.3**: Refactor story_structure.py (1,318 lines → 3-4 files)
- Create StoryRepository, StoryService, StructureAnalyzer
- Split routes: crud.py, analysis.py, validation.py

---

### Phase 4: Provider Consistency
**Goal**: Eliminate duplication across 8 AI providers
**Priority**: MEDIUM - Improves maintainability
**Estimated Tasks**: 9

**Task 4.1**: Refactor OpenAI Provider (774 lines)
- Use shared retry/polling/auth utilities from P0.1.4
- Target: ~400 lines

**Task 4.2**: Refactor Keling Provider (843 lines)
- Use shared utilities
- Target: ~400 lines

**Task 4.3**: Refactor VolcEngine Provider (1,409 lines → split?)
- Consider splitting into image/video sub-providers
- Use shared utilities
- Target: ~400 lines per file if split, or ~500 if not

**Task 4.4-4.8**: Refactor Remaining Providers
- Jimeng, MiniMax, DeepSeek, Google, Aliyun OSS
- Consistent pattern across all

---

### Phase 5: Page Component Refactoring (Frontend)
**Goal**: Apply container/presentation split to remaining large pages
**Priority**: MEDIUM
**Estimated Tasks**: 6

**Task 5.1**: Refactor episodes/[id]/page.tsx (1,580 lines)
- Create useEpisode hook
- Extract EpisodeHeader, ScriptList, GenerationPanel components
- Target: < 200 lines

**Task 5.2**: Refactor virtual-ip/[id]/images/page.tsx (1,143 lines)
- Create useImageGallery hook
- Extract ImageGrid, GenerationModal, SelectionPanel components
- Target: < 200 lines

**Task 5.3**: Refactor scripts/[id]/page.tsx (705 lines)
- Create useScript hook
- Extract ScriptEditor, VersionHistory components
- Target: < 200 lines

**Task 5.4**: Refactor virtual-ip/[id]/page.tsx (717 lines)
- Extract sub-components
- Target: < 200 lines

**Task 5.5**: Refactor stories/page.tsx (620 lines)
- Extract StoryCard, StoryFilters components
- Target: < 200 lines

**Task 5.6**: Refactor stories/[id]/page.tsx (606 lines)
- Extract StoryDetails, ChapterList components
- Target: < 200 lines

---

### Phase 6: Testing & Documentation
**Goal**: Ensure quality and maintainability of refactored code
**Priority**: ONGOING - Do incrementally with each phase
**Estimated Tasks**: Continuous

**For Each Refactoring Task:**
1. Write/update unit tests for new services/hooks
2. Write/update integration tests for new endpoints
3. Add JSDoc/docstrings with examples
4. Update architecture docs if patterns change

**Specific Tasks:**
- Add OpenAPI documentation generation
- Create component storybook (future)
- Write refactoring ADRs (Architecture Decision Records)

---

## Execution Strategy

### Incremental Approach
- **Do NOT refactor everything at once**
- Complete Phase 0 entirely before starting Phase 1
- Within each phase, complete one task fully (code + tests + docs) before starting next
- Each task should be a separate PR with ledger entry

### Backward Compatibility
- Use deprecation warnings before removing old code
- Maintain API compatibility during transitions
- Update all callers before deleting old code

### Testing Strategy
- All refactored code must maintain or improve test coverage
- Run full test suite after each task
- Add regression tests for bug fixes discovered during refactoring

### Documentation Updates
- Update AGENTS.md examples as better patterns emerge
- Document new patterns in architecture docs
- Create migration guides for major changes

---

## Success Metrics

### Quantitative Goals
- [ ] No Python file exceeds 300 lines (currently 10+ violations)
- [ ] No TypeScript file exceeds 250 lines (currently 6+ violations)
- [ ] Backend average file size: 150-250 lines (currently ~380)
- [ ] Frontend average file size: 100-200 lines (currently ~435)
- [ ] Test coverage maintained at 80%+ (backend)
- [ ] Test coverage established at 70%+ (frontend)

### Qualitative Goals
- [ ] Clear separation of concerns (API → Service → Repository → Model)
- [ ] Consistent patterns across all providers
- [ ] No code duplication (< 3 occurrences before extraction)
- [ ] All endpoints follow thin controller pattern
- [ ] All components follow container/presentation split

---

## Risk Mitigation

### High-Risk Areas
1. **scripts.py refactoring**: 68 functions with complex interdependencies
   - Mitigation: Extensive integration tests before splitting
2. **storyboard/page.tsx**: 100+ state variables with complex interactions
   - Mitigation: Feature flags for gradual rollout
3. **API client split**: Breaking change potential for all frontend code
   - Mitigation: Maintain backward compatibility during transition

### Rollback Strategy
- Keep old code in separate files during transition
- Use feature flags where applicable
- Tag working commits before major refactorings

---

## Phase 0 Quick Start (Next Steps)

To begin refactoring, start with these foundation tasks in order:

1. **Task 0.1.2**: Create `core/exceptions.py` (easiest, no dependencies)
2. **Task 0.1.3**: Create exception middleware (depends on 0.1.2)
3. **Task 0.1.1**: Create repository base classes
4. **Task 0.1.4**: Extract shared provider utilities
5. **Task 0.2.1**: Create base Modal component
6. **Task 0.2.2**: Create foundation hooks
7. **Task 0.2.4**: Organize component directories
8. **Task 0.2.3**: Split API client phase 1

**Estimated Phase 0 Duration**: This establishes the foundation. Complete all 8 tasks before moving to Phase 1.

**First High-Impact Win**: After Phase 0, tackle Task 1.1 (scripts.py) or Task 1.2 (storyboard page) for immediate visible improvement.

---

## Appendix: Complete Task List by File

### Backend Files Requiring Refactoring (Priority Order)

| File | Current Lines | Target Files | Target Lines | Phase |
|------|--------------|--------------|--------------|-------|
| scripts.py | 4,168 | 8-10 files | ~300 each | P1.1 |
| ai_service.py | 2,910 | 5-6 files | ~250 each | P2.1 |
| episodes.py | 1,605 | 4-5 files | ~250 each | P3.1 |
| volcengine_provider.py | 1,409 | 1-2 files | ~400 each | P4.3 |
| virtual_ip_images.py | 1,364 | 3-4 files | ~250 each | P3.2 |
| story_structure.py | 1,318 | 3-4 files | ~250 each | P3.3 |
| ai_service_manager.py | 1,301 | 2-3 files | ~250 each | P2.1 |
| dialogue_audio_service.py | 1,261 | 3 files | ~300 each | P2.2.1 |
| voice_catalog.py | 1,171 | 3 files | ~250 each | P2.2.2 |
| keling_provider.py | 843 | 1 file | ~400 | P4.2 |
| openai_provider.py | 774 | 1 file | ~400 | P4.1 |

### Frontend Files Requiring Refactoring (Priority Order)

| File | Current Lines | Target Files | Target Lines | Phase |
|------|--------------|--------------|--------------|-------|
| storyboard/page.tsx | 3,279 | 10+ files | ~200 each | P1.2 |
| api.ts | 2,627 | 15+ files | ~200 each | P2.3 |
| episodes/[id]/page.tsx | 1,580 | 5-6 files | ~200 each | P5.1 |
| virtual-ip/[id]/images/page.tsx | 1,143 | 4-5 files | ~200 each | P5.2 |
| virtual-ip/[id]/page.tsx | 717 | 3-4 files | ~200 each | P5.4 |
| scripts/[id]/page.tsx | 705 | 3-4 files | ~200 each | P5.3 |
| stories/page.tsx | 620 | 2-3 files | ~200 each | P5.5 |
| stories/[id]/page.tsx | 606 | 2-3 files | ~200 each | P5.6 |

---

**Total Estimated Files to Create/Refactor**: 100+
**Total Estimated Line Reduction**: ~15,000 lines through better organization
**Total Estimated New Shared Utilities**: ~2,000 lines

**Net Result**: Same functionality, better organized, more maintainable, aligned with AGENTS.md standards.
