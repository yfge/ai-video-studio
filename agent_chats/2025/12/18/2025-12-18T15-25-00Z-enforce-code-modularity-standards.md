---
id: 2025-12-18T15-25-00Z-enforce-code-modularity-standards
date: 2025-12-18T15:25:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [docs, architecture, standards, refactor]
related_paths:
  - AGENTS.md
summary: "Added strict code architecture and quality standards to enforce modularity and prevent monolithic files"
---

## User Prompt

User requested to add strict guidelines in AGENTS.md regarding:
- File size limits
- Code structure and modularity
- Code reuse
- Proactive refactoring

Context: Code analysis showed ai-video-studio (fully AI-generated) produced larger, more monolithic files (avg 380-435 lines/file) compared to ai-shifu (human + AI, avg 119-186 lines/file). User wanted to enforce better practices going forward.

## Goals

1. Add comprehensive code quality standards section to AGENTS.md
2. Define strict file size limits for Python and TypeScript files
3. Enforce single responsibility principle
4. Mandate proactive refactoring and code reuse
5. Use ai-shifu metrics as reference standard
6. Make these requirements mandatory for all future development

## Changes

### Added "Code Architecture & Quality Standards (CRITICAL)" Section

Location: AGENTS.md after "Repository Expectations", before "Agent Collaboration Ledger"

Key requirements added:

**File Size Limits (Strict)**
- Python files: MAX 300 lines (target 150-250)
- TypeScript/TSX files: MAX 250 lines (target 100-200)
- Immediate refactoring required when approaching limits

**Single Responsibility Principle (Mandatory)**
- One file, one purpose
- API routes < 50 lines
- Extract business logic to services
- Separate presentation from logic in React components

**Code Reuse & DRY**
- Proactive duplication detection
- Extract shared utilities before third occurrence
- Defined common patterns for backend/frontend organization

**Mandatory Refactoring Triggers**
1. File exceeds size limit
2. Function exceeds 50 lines
3. Duplicate code in 3+ places
4. Nested conditionals > 3 levels
5. God objects detected
6. Import cycles

**Modular Architecture Best Practices**
- Vertical slicing by feature/domain
- Explicit interfaces via schemas
- Proper dependency direction
- No circular dependencies

**Reference Standard: ai-shifu**
- Backend: 186 lines/file (183 files)
- Frontend: 119 lines/file (258 files)
- Target: match or exceed this modularity

**Enforcement**
- Agent self-audit before completion
- Document refactoring in agent_chats with [refactor] tag
- Future TODO: pre-commit hooks for file size limits

## Validation

1. ✅ AGENTS.md updated with new section
2. ✅ CLAUDE.md automatically synced (symlink)
3. ✅ GEMINI.md automatically synced (symlink)
4. ✅ Section placed in logical location (after Repository Expectations)
5. ✅ Content is actionable and specific
6. ✅ References real metrics from codebase analysis

No code changes involved, only documentation update.

## Next Steps

1. Commit AGENTS.md change with this ledger entry
2. In future development, agents must follow these standards strictly
3. Consider implementing pre-commit hook to enforce file size limits automatically
4. When refactoring existing large files, create separate tickets/ledger entries with [refactor] tag
5. Monitor compliance in future code reviews

## Linked Commits

Will be added after commit is created.
