# Agents Guidance for ai-video-studio

This document is the single source of truth for every coding assistant (Claude Code, Codex, Gemini, Cursor, etc.) that collaborates on this repository. Keep this file authoritative and avoid duplicating instructions elsewhere; all agent-specific instruction files must reference this document.

## Instruction Precedence & Mirrors

- Respect instruction order: system / developer → user → this file → everything else.
- The following files must be kept as symlinks (or exact copies) of `AGENTS.md`: `CLAUDE.md`, `GEMINI.md`.
- When this file is updated, ensure mirrored files stay in sync within the same commit.

## Atomic Commit Discipline (Critical)

- Stage and commit every atomic change **immediately** after completing validation; do not carry pending edits while starting new tasks.
- Pair each commit with its corresponding `agent_chats` ledger entry inside the same commit.
- Keep the working tree clean at all times—no stray modifications or half-staged files between commits.
- If a change cannot be validated yet, park it on a feature branch instead of leaving it unstaged.

## Mission & Scope

ai-video-studio is an AI-powered virtual IP production platform composed of:

- `ai-pic-backend/`: FastAPI + SQLAlchemy service orchestrating AI image/video generation, story workflows, and OSS persistence.
- `ai-pic-frontend/`: Next.js 15 (App Router) application for operators to manage virtual IPs, galleries, stories, episodes, and scripts.

The codebase must remain production-grade, auditable, and reproducible. Every meaningful code change needs traceable documentation, automated validation, and a matching ledger entry.

## Repository Expectations

- **Backend layout**: `app/` (core, api, models, schemas, services), `alembic/`, `tests/`, `scripts/`. Keep service/business logic in `app/services/`; APIs remain thin.
- **Frontend layout**: `src/app/`, `src/components/`, `src/lib/`, `src/utils/`. Keep UI state colocated with features; limit global state.
- **Testing**: Maintain comprehensive pytest coverage (`ai-pic-backend`) and Next.js lint rules. Backend changes must pass `pytest`; frontend changes must pass `npm run lint`.
- **Docs**: Update README / guides when behaviour changes. Architecture decisions belong under `docs/` (create if missing) and should be cross-linked from agent chats.
- **Tasks.md is canonical**: Maintain the live task board in `tasks.md` (use `[ ]` for未完成、`[x]`为已完成). Merge/append所有任务到该文件，禁止再用旧的 `task.md`。

## Code Architecture & Quality Standards (CRITICAL)

**Context**: Analysis shows AI-generated code in this project initially produced large, monolithic files (avg 380-435 lines/file) compared to human-written codebases like ai-shifu (avg 119-186 lines/file). This section enforces modular, maintainable architecture.

### File Size Limits (Strict)

- **Python files**: MUST NOT exceed 300 lines (excluding docstrings/comments). Target: 150-250 lines.
- **TypeScript/TSX files**: MUST NOT exceed 250 lines. Target: 100-200 lines.
- **When a file approaches the limit**: IMMEDIATELY refactor before adding new code.
- **Exception**: Only with explicit user approval and documented rationale in commit message.

### Single Responsibility Principle (Mandatory)

- **One file, one purpose**: Each module should have a single, well-defined responsibility.
- **API endpoints**: Keep route handlers thin (< 50 lines). Extract business logic to services.
- **React components**: Separate presentation from logic. Use custom hooks for complex state.
- **Service modules**: One service class per domain concept (e.g., `virtual_ip_service.py`, not `services.py`).

### Code Reuse & DRY (Do Not Repeat Yourself)

- **Detect duplication proactively**: Before writing similar code a third time, extract to shared utility.
- **Common patterns**:
  - Backend: Shared validation logic → `app/core/validators/`
  - Backend: Common DB queries → repository pattern in services
  - Frontend: Repeated UI patterns → `src/components/ui/` or `src/components/shared/`
  - Frontend: Business logic → `src/lib/` or custom hooks in `src/hooks/`
- **Prefer composition over inheritance**: Use mixins, utility functions, and HOCs.

### Mandatory Refactoring Triggers

Refactor IMMEDIATELY (before continuing with new features) when ANY of these occur:

1. **File exceeds size limit** (see above)
2. **Function exceeds 50 lines**: Extract sub-functions or split responsibilities
3. **Duplicate code in 3+ places**: Create shared utility
4. **Nested conditionals > 3 levels**: Refactor to early returns or strategy pattern
5. **God object detected**: Split into multiple focused modules
6. **Import cycles**: Restructure dependencies

### Modular Architecture Best Practices

- **Vertical slicing**: Group by feature/domain, not by technical layer alone
  - Good: `services/virtual_ip/`, `services/story/`, `services/gallery/`
  - Bad: `services/business_logic.py` with all domains mixed
- **Explicit interfaces**: Use Pydantic schemas, TypeScript interfaces for contracts
- **Dependency direction**: High-level modules must not depend on low-level details
- **No circular dependencies**: Enforce with linters; restructure if detected

### Reference Standard: ai-shifu Codebase

- **ai-shifu metrics**: Backend 186 lines/file (183 files), Frontend 119 lines/file (258 files)
- **Target alignment**: Match or exceed ai-shifu's modularity. When in doubt, split files.
- **Learning**: Study ai-shifu's structure for inspiration on how to decompose features.

### Enforcement

- **Pre-commit hooks**: Add linters to flag files exceeding size limits (TODO: implement)
- **Code review mindset**: Every new file must justify its size and scope
- **Agent self-audit**: Before marking work complete, review all touched files for compliance
- **Ledger requirement**: Document refactoring decisions in `agent_chats` with `[refactor]` tag

**Remember**: Small, focused files are easier to test, review, reuse, and maintain. Over-sized files are technical debt. Proactive refactoring is not optional—it's a core responsibility.

## Backend-Specific Architecture Standards (CRITICAL)

**Current State**: Analysis identified critical violations requiring immediate attention in future work.

### API Endpoint Organization

**CRITICAL Violations Identified:**
- `scripts.py`: 4,168 lines with 68 functions (14x limit) - handles scripts, episodes, storyboards, dialogue, video generation
- `episodes.py`: 1,605 lines
- `virtual_ip_images.py`: 1,364 lines
- `story_structure.py`: 1,318 lines

**Mandatory Pattern - Thin Controllers:**
- **Route handlers MUST NOT exceed 50 lines**
- **One route file per resource**: Split by domain (scripts → script_crud.py, script_generation.py, script_export.py)
- **Extract business logic to services**: No DB queries, AI calls, or complex logic in endpoints
- **Use dependency injection**: Pass services via FastAPI `Depends()`
- **Standard structure per endpoint**:
  ```python
  @router.post("/resource")
  async def create_resource(
      data: ResourceCreate,
      service: ResourceService = Depends(get_resource_service)
  ):
      """Docstring with examples."""
      return await service.create(data)
  ```

**Refactoring Priority (for future work):**
1. Split `scripts.py` into 8-10 focused endpoint files
2. Extract business logic from endpoints into dedicated services
3. Create shared validators for common patterns

### Service Layer Organization

**CRITICAL Violations Identified:**
- `ai_service.py`: 2,910 lines (God object)
- `ai_service_manager.py`: 1,301 lines
- `dialogue_audio_service.py`: 1,261 lines
- `voice_catalog.py`: 1,171 lines

**Mandatory Service Patterns:**
- **One service per domain entity**: `ScriptService`, `EpisodeService`, `StoryboardService` (not `AIService` for everything)
- **Service file limit**: 250 lines (stricter than general 300-line limit)
- **Repository pattern for data access**: Create `repositories/` for DB query encapsulation
  ```python
  # Good structure:
  services/
    script/
      script_service.py       (< 250 lines)
      script_generator.py     (< 250 lines)
      script_validator.py     (< 250 lines)
    episode/
      episode_service.py      (< 250 lines)
      episode_processor.py    (< 250 lines)
  ```
- **Separation of concerns**:
  - Business logic → services
  - Data access → repositories
  - External API calls → providers
  - Validation → validators (in `core/validators/`)
  - Transformations → utils

### Provider Pattern Consistency (8 AI Providers)

Current providers: OpenAI, Google, DeepSeek, MiniMax, Keling, Jimeng, VolcEngine (1,409 lines!), Aliyun OSS

**Mandatory Standards:**
- **All providers MUST extend `BaseProvider`**
- **Consistent error handling**: Use shared `ProviderError` hierarchy
- **Shared retry logic**: Extract to `core/retry_utils.py` (max 150 lines)
- **Shared auth patterns**: Abstract credential management
- **Consistent logging**: Use structured logging with provider name tag
- **Polling utilities**: Share async job polling logic in `core/polling_utils.py`
- **Provider file limit**: 400 lines (complex integrations allowed slightly larger, but must justify)

**Pattern to follow**:
```python
class ConcreteProvider(BaseProvider):
    def __init__(self): pass  # Auth setup
    async def generate(self): pass  # Main operation
    async def _handle_error(self): pass  # Error mapping
    async def _poll_job(self): pass  # Use shared polling utility
```

**Code Reuse Targets:**
- Auth header construction (duplicated 8x)
- Request/response logging (duplicated 8x)
- Retry with exponential backoff (duplicated 8x)
- URL normalization (`_abs_url` patterns duplicated)

### Model & Schema Organization

**Current State**: 17 files, well-organized but could improve

**Standards**:
- **One model per file** (already followed, good!)
- **Schema files mirror model files**: `models/script.py` → `schemas/script.py`
- **Schema file limit**: 300 lines. If exceeded, split into `script_base.py`, `script_create.py`, `script_response.py`
- **Use schema inheritance**: Create `BaseSchema` with common fields (id, created_at, updated_at)
- **No business logic in models**: Models are data structures only

### Database & Repository Pattern

**Current Issue**: DB queries scattered across endpoints and services (212+ direct SQLAlchemy calls)

**Mandatory Pattern** (for new code):
- **Create `repositories/` directory**: One repository per model
- **Encapsulate all DB access**: No `session.query()` outside repositories
- **Repository interface**:
  ```python
  class ScriptRepository:
      def __init__(self, session: Session): pass
      async def get_by_id(self, id: int): pass
      async def list_by_user(self, user_id: int): pass
      async def create(self, data: dict): pass
      async def update(self, id: int, data: dict): pass
      async def soft_delete(self, id: int): pass
  ```
- **Services use repositories**: Services never touch SQLAlchemy directly
- **Transaction management**: Repositories handle commits/rollbacks

### Error Handling

**Current Issue**: 212 `HTTPException` raises scattered across code, no consistency

**Mandatory Standards**:
- **Centralized exception classes**: Create `core/exceptions.py` with domain exceptions
  ```python
  class ScriptNotFoundError(DomainError): pass
  class GenerationFailedError(DomainError): pass
  ```
- **Exception middleware**: Convert domain exceptions to HTTP responses in middleware
- **No direct HTTPException**: Endpoints raise domain exceptions, middleware converts
- **Structured error responses**: Use Pydantic schema for error format

## Frontend-Specific Architecture Standards (CRITICAL)

**Current State**: Next.js 15 App Router with significant violations requiring immediate attention in future work.

### Page Component Size Limits

**CRITICAL Violations Identified:**
- `storyboard/page.tsx`: 3,279 lines with 100+ state variables (13x limit!)
- `episodes/[id]/page.tsx`: 1,580 lines
- `virtual-ip/[id]/images/page.tsx`: 1,143 lines
- `scripts/[id]/page.tsx`: 705 lines

**Mandatory Pattern - Container/Presentation Split:**
- **Page components MUST NOT exceed 200 lines**
- **Extract feature logic to custom hooks**: `useStoryboard()`, `useEpisodeManager()`
- **Split into sub-components**: One component per logical section
- **Page responsibility**: Routing, layout, data fetching coordination ONLY

**Example Refactoring** (for storyboard page):
```typescript
// storyboard/page.tsx (< 200 lines)
export default function StoryboardPage() {
  return (
    <StoryboardProvider>
      <StoryboardLayout>
        <StoryboardTimeline />
        <StoryboardFrameGrid />
        <StoryboardModals />
      </StoryboardLayout>
    </StoryboardProvider>
  )
}

// hooks/useStoryboard.ts (< 250 lines)
export function useStoryboard() {
  // State management logic
}

// components/storyboard/Timeline.tsx (< 200 lines)
// components/storyboard/FrameGrid.tsx (< 200 lines)
// components/storyboard/Modals.tsx (< 150 lines)
```

### Component Organization

**Current Issue**: 21 components at root of `components/`, no organization

**Mandatory Structure:**
```
src/
  components/
    ui/                 (Reusable primitives)
      Button.tsx
      Modal.tsx
      Card.tsx
    shared/             (Shared business components)
      ImageSelector.tsx
      ModelPicker.tsx
    features/           (Feature-specific components)
      storyboard/
        Timeline.tsx
        FrameGrid.tsx
      virtual-ip/
        ImageGallery.tsx
        GenerationPanel.tsx
    layouts/            (Layout components)
      AdminLayout.tsx
      DashboardLayout.tsx
```

**Rules:**
- **ui/**: Pure presentational, no business logic, < 150 lines
- **shared/**: Reusable across features, < 200 lines
- **features/**: Feature-specific, colocated with domain logic, < 250 lines
- **One component per file**: No multiple exports unless tightly coupled (e.g., Item and ItemList)

### Custom Hooks

**Current Issue**: Only 3 hooks, massive opportunity for extraction

**Mandatory Patterns:**
- **Extract repeated useState patterns**: If 3+ components use similar state, create hook
- **API call hooks**: `useScript()`, `useEpisode()`, `useVirtualIP()`
- **Form hooks**: `useScriptForm()`, `useGenerationForm()`
- **Modal hooks**: `useModal()` for open/close/data state
- **Hook file limit**: 200 lines per hook file

**Common hooks to create:**
- `useApi()`: Wraps fetch with error handling
- `useAsyncTask()`: Manages loading/error/data state
- `usePolling()`: Polls backend for task status
- `useToast()`: Centralized toast notifications
- `useConfirm()`: Confirmation dialogs

### API Client Organization

**CRITICAL Violation:**
- `utils/api.ts`: 2,627 lines with 100+ interface definitions (10x limit!)

**Mandatory Refactoring Pattern:**
```
utils/
  api/
    client.ts           (HTTP client, < 150 lines)
    types/              (Split by domain)
      script.types.ts   (< 200 lines)
      episode.types.ts  (< 200 lines)
      virtual-ip.types.ts (< 200 lines)
    endpoints/          (API functions by domain)
      scripts.ts        (< 250 lines)
      episodes.ts       (< 250 lines)
      virtual-ip.ts     (< 250 lines)
```

**Standards:**
- **Type definitions separate from API calls**
- **One file per domain resource**
- **Shared error handling**: Centralized in `client.ts`
- **Auth token management**: In client, not scattered

### State Management

**Current Pattern**: Local state with direct API calls (100+ useState in storyboard page)

**Standards for Complex Features:**
- **Use React Context for shared state**: Modal state, alerts, user context
- **Consider React Query for server state**: Caching, revalidation, background updates
- **Local state for UI only**: Form inputs, modal open/close, UI toggles
- **Props drilling limit**: If passing props > 2 levels deep, use Context

**When to use what:**
- Simple forms: Local `useState`
- Multi-step forms: `useReducer` or form library (React Hook Form)
- Shared UI state (modals, alerts): Context
- Server data: React Query or SWR
- Complex feature state: Custom hook + Context

### Modal Component Pattern

**Current Issue**: 5 similar modal components with duplicated structure (UserDetailsModal, UserApprovalModal, etc.)

**Mandatory Pattern:**
```typescript
// components/ui/Modal.tsx (base modal, < 100 lines)
export function Modal({ isOpen, onClose, title, children }) { }

// components/shared/modals.tsx (specialized modals)
export function UserDetailsModal() {
  return <Modal title="User Details">{/* content */}</Modal>
}
```

**Rules:**
- **Extract common modal wrapper**: Header, footer, close button, backdrop
- **Modal content < 150 lines**: If exceeded, split content into separate components
- **Consistent modal API**: All modals use same open/close/data pattern

## Testing Standards (Mandatory)

**Current State**: 75 backend test files, 0 frontend tests

### Backend Testing

**Directory Structure** (mirrors source):
```
tests/
  unit/               (Isolated unit tests)
    services/         (Mirror app/services/)
    models/           (Mirror app/models/)
    utils/            (Mirror app/utils/)
  integration/        (Multi-service tests)
    api/              (Mirror app/api/)
  e2e/                (End-to-end flows)
```

**Standards:**
- **Test file naming**: `test_<module_name>.py` (e.g., `test_script_service.py`)
- **One test file per source file**: Maintain 1:1 mapping
- **Use pytest markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`, `@pytest.mark.slow`
- **Coverage target**: 80% (enforced in pytest.ini)
- **Test structure**: Arrange/Act/Assert with clear comments

### Frontend Testing (TODO - Not Implemented)

**Mandatory Setup** (for future implementation):
- **Install testing library**: `@testing-library/react`, `@testing-library/jest-dom`
- **Test structure**: `src/__tests__/` mirroring `src/` structure
- **Component tests**: Render + interaction + assertions
- **Hook tests**: Use `@testing-library/react-hooks`
- **Coverage target**: 70% for new code

## Documentation Standards

**Current State**: `docs/` is the authoritative home for design/testing/provider notes; keep `docs/README.md` current.

### Docs Index (Authoritative)
- `docs/README.md` — canonical index for all docs (update on add/remove).
- `docs/TESTING_GUIDE.md` — required browser E2E validation steps.
- `docs/story-structure-api.md` — normalized story-structure endpoints.
- `docs/storyboard-normalized-toggle.md` — storyboard normalized integration notes.
- `docs/story-structure-gap-analysis.md` — historical gap analysis (pre-normalization).
- `docs/dialogue-audio-timeline-spec.md` — dialogue audio + timeline spec.
- `docs/timeline-rendering-pipeline.md` — timeline/rendering pipeline design.
- `docs/soft-delete-business-id.md` — soft delete + business_id design.
- `docs/api/` — provider API references (Volcengine, Keling, Minimax, etc.).

**Mandatory Requirements:**

### API Documentation
- **Add OpenAPI/Swagger**: Generate from Pydantic schemas (`/docs` endpoint)
- **Endpoint docstrings**: Include request/response examples
- **Schema descriptions**: Add `description` field to all Pydantic models

### Component Documentation
- **JSDoc for public components**: Document props, usage, examples
- **Storybook** (future): Component library with live examples
- **README per feature directory**: Explain architecture decisions

### Architecture Documentation
- **ADR (Architecture Decision Records)**: Document major decisions in `docs/adr/`
- **Update existing docs**: When changing behavior referenced in docs

## Code Review Checklist (For Agents)

Before marking work complete and creating ledger entry, verify:

### Size Compliance
- [ ] No Python file exceeds 300 lines
- [ ] No TypeScript/TSX file exceeds 250 lines
- [ ] No service file exceeds 250 lines
- [ ] No API endpoint file has routes > 50 lines each
- [ ] No page component exceeds 200 lines

### Structure Compliance
- [ ] Single responsibility: Each file has one clear purpose
- [ ] No code duplication: Repeated code (3+ occurrences) extracted to shared utility
- [ ] Proper layering: API → Service → Repository → Model
- [ ] No circular dependencies

### Testing Compliance
- [ ] Test file exists for new source file (backend)
- [ ] Tests pass: `pytest` for backend, `npm run lint` for frontend
- [ ] Coverage maintained or improved

### Documentation Compliance
- [ ] Docstrings added for new public functions/classes
- [ ] Type hints added (Python) or TypeScript types defined
- [ ] Updated relevant markdown docs if behavior changed

### Ledger Compliance
- [ ] Agent chat ledger entry created in `agent_chats/YYYY/MM/DD/`
- [ ] Frontmatter complete with all required fields
- [ ] All sections present: User Prompt, Goals, Changes, Validation, Next Steps, Linked Commits
- [ ] If refactoring, tagged with `[refactor]`

**If ANY checklist item fails, do NOT mark work complete. Fix violations first.**

## Agent Collaboration Ledger (`agent_chats/`)

We operate with the same rigor as the reference repositories (`talkReplay`, `orion`, `ai-shifu`, `talkreplay.com`). Follow these rules exactly:

1. Directory structure: `agent_chats/YYYY/MM/DD/`. Create folders as needed; never place files directly under `agent_chats/`.
2. File naming: `YYYY-MM-DDTHH-MM-SSZ-kebab-topic.md` (UTC timestamps). Example: `2025-10-23T07-30-03Z-backend-fastapi-refactor.md`.
3. YAML frontmatter is **required**:
   ```yaml
   ---
   id: 2025-10-23T07-30-03Z-backend-fastapi-refactor
   date: 2025-10-23T07:30:03Z
   participants: [human, codex]
   models: [gpt-4o-mini]
   tags: [backend, api]
   related_paths:
     - ai-pic-backend/app/api/v1/virtual_ip.py
   summary: "Refined virtual IP endpoints and added validation"
   ---
   ```
4. Body sections (all mandatory and in order):
   - `## User Prompt`
   - `## Goals`
   - `## Changes`
   - `## Validation`
   - `## Next Steps`
   - `## Linked Commits`
5. Reference all touched files under `related_paths` using repository-relative paths.
6. Every commit that touches code in `ai-pic-backend/`, `ai-pic-frontend/`, `scripts/`, or modifies this document must include at least **one** staged ledger entry.
7. **Atomic commits are non-negotiable:** after completing each atomic piece of work, stage the matching files and commit immediately. Keep commits minimal, focused, and easily traceable with their corresponding ledger record.
8. Keep `agent_chats/` clean: no unstaged edits, no binary files, redact secrets, prefer ASCII.

The helper `scripts/check_agent_chats.py` (wired into pre-commit) enforces naming, frontmatter, and section requirements. The hook fails when code changes lack a matching ledger entry or when ledger files are malformed.
- 在提交前执行 `./docker/build_prod_images.sh`，确保生产镜像可构建；构建失败需先修复后再提交。

## Pre-Commit Gates & Quality Bar

We adopt a strict workflow similar to the reference projects:

- Install `pre-commit` locally (`pip install pre-commit`) and run `pre-commit install` once.
- Hooks run automatically:
  - `ruff`, `isort`, and `black` for Python under `ai-pic-backend/`.
  - `prettier` for Markdown/JSON/YAML/TypeScript styles.
  - `scripts/check_agent_chats.py` for ledger compliance.
  - `pytest` (backend quick gate) whenever staged files live under `ai-pic-backend/`.
  - `npm run lint` when staging files under `ai-pic-frontend/src/`.
  - `commitlint` enforces Conventional Commit subjects on commit messages.
- Do **not** circumvent hooks. Fix violations or explicitly document why a file is exempt (rare, with user approval).

## Backend Workflow (`ai-pic-backend/`)

1. Use a Python 3.11+ environment.
2. Install dependencies: `pip install -r requirements.txt -r requirements-test.txt`.
3. Run tests before every commit touching backend code:
   ```bash
   cd ai-pic-backend
   pytest
   ```
4. Additional diagnostics available:
   - `python run_tests.py quick` for lightweight checks.
   - `python manage.py migration status` before/after schema work.
   - `pytest tests/test_fastapi_full_flow.py::test_fastapi_full_image_generation_flow -v` for the full AI pipeline.
5. Update docs (`TESTING_GUIDE.md`, `MIGRATION_SYSTEM_GUIDE.md`, etc.) when workflows change.

## Frontend Workflow (`ai-pic-frontend/`)

1. Node.js 20 LTS + npm.
2. Install dependencies: `cd ai-pic-frontend && npm install`.
3. Validate UI work:
   - `npm run lint`
   - `npm run test` (add/maintain tests as the suite grows)
   - `npm run dev` for local verification prior to committing.
4. Keep Tailwind tokens consistent; avoid ad-hoc styling. Update component docs if behaviour changes.

## Commit & Branch Policy

- Conventional Commit messages (lowercase type, ≤72 chars). Examples: `feat(backend): add retry policy`, `fix(frontend): guard auth redirects`.
- **Commit immediately after each atomic change; never postpone commits or leave work-in-progress unstaged.**
- **Atomic commits are mandatory:** once a work item is complete, commit it before starting anything else. Do not batch unrelated tasks into a single commit.
- Always stage the matching `agent_chats` entry with the code changes.
- Prefer focused commits; large changes should be split logically and each accompanied by its own ledger entry.
- Treat `main` as protected: work in topic branches (`feat/*`, `fix/*`, `chore/*`) when collaborating.

### CRITICAL — Minimal Atomic Commits & Clean Workspace

- Minimal atomic commits only: one logical change per commit, paired with its ledger entry. Do not bundle unrelated edits.
- **Keep the repository clean in real time: commit each atomic unit the moment it is complete; never leave stray work sitting unstaged.**
- Minimize diff scope: touch only the files/lines necessary for the task; avoid opportunistic refactors or drive‑by style changes.
- Keep the working tree clean: before each commit ensure there are no stray unstaged edits. Do not leave the repo dirty between steps.

## Delivery Checklist for Agents

Before yielding work back to the user:

**CRITICAL — Chrome self-test (MCP):** After completing each functional change, run a quick end-to-end verification using Chrome via MCP/DevTools; record the scenario in `agent_chats` before marking the task done. Use test account `geyunfei` / `Gyf@845261` to log in. Do not defer runs due to model cost—assume budget is OK.

**CRITICAL — 不要嘴硬:** 当日志、请求结果或用户现场信息与你的推断不一致时，**优先承认不确定性和可能的误判，先复盘/排查，再给结论**；禁止反复坚持“代码没问题”“环境有问题”这类口头判断。遇到冲突信号时，要主动用真实请求（curl、自测脚本、浏览器实际路径）复现问题，并在 `agent_chats` 的 `## Validation` 段明确记录你是如何验证和纠正自己的。

1. Ensure relevant tests (`pytest`, `npm run lint`, targeted suites) pass locally.
2. Verify `pre-commit run --all-files` is clean or document any justified skips.
2.1 Ensure the working tree is clean (no unstaged changes) at commit time.
3. Confirm new/updated `agent_chats` entries satisfy format rules and describe intent, changes, validation, and follow-ups.
4. For任何涉及前后端联动、登录、AI 调用/图像生成等功能改动，**必须在真实浏览器（推荐 Chrome）中完成至少一次端到端路径验证**，可以通过 DevTools 自动化/远程调试完成；在 `agent_chats` 的 `## Validation` 段中明确记录所走用例（例如使用 Seedream 4.5 在虚拟 IP 图像页生成图片的步骤和结果）。
5. Summarise remaining risks or TODOs in the agent response。
6. Never commit secrets or credentials; reference environment variables instead.

Following these conventions keeps the repo aligned with the rigor demonstrated in `talkReplay`, `orion`, `ai-shifu`, and `talkreplay.com`. Deviations require explicit user approval and should be documented in the ledger and commit messages.
