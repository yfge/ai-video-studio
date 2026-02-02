---
id: 2026-02-02T09-45-00Z-frontend-readiness-integration
date: 2026-02-02T09:45:00Z
participants: [human, claude-opus-4-5]
models: [claude-opus-4-5-20251101]
tags: [frontend, readiness-check, quick-fix, episode-generation]
related_paths:
  - ai-pic-frontend/src/utils/api/types/story.types.ts
  - ai-pic-frontend/src/utils/api/endpoints/story.endpoints.ts
  - ai-pic-frontend/src/components/features/story-detail/StoryReadinessPanel.tsx
  - ai-pic-frontend/src/components/features/story-detail/EpisodeGeneratePanel.tsx
  - ai-pic-frontend/src/components/features/story-detail/index.ts
  - ai-pic-frontend/src/components/features/index.ts
  - ai-pic-frontend/src/hooks/useStoryReadiness.ts
  - ai-pic-frontend/src/hooks/useStoryDetail.ts
  - ai-pic-frontend/src/app/stories/[id]/page.tsx
summary: "Integrated Phase 3 readiness check and quick-fix APIs into frontend episode generation flow"
---

## User Prompt

Continue from previous conversation - integrate the readiness check and quick-fix APIs with the frontend episode generation flow.

## Goals

1. Add readiness check types to frontend API types
2. Add readiness check and quick-fix API endpoints
3. Create StoryReadinessPanel component to display check results
4. Create useStoryReadiness hook for readiness logic
5. Integrate readiness panel into episode generation flow
6. Block generation when critical issues exist, provide quick-fix button

## Changes

### New Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `src/components/features/story-detail/StoryReadinessPanel.tsx` | ~170 | Displays readiness check results with severity badges, quick-fix preview/apply |
| `src/hooks/useStoryReadiness.ts` | ~90 | Hook for readiness check and quick-fix state management |

### Modified Files

| File | Change |
|------|--------|
| `src/utils/api/types/story.types.ts` | Added ReadinessCheck, ReadinessResult, QuickFix* types |
| `src/utils/api/endpoints/story.endpoints.ts` | Added checkStoryReadiness, checkEpisodeReadiness, quickFixStory functions |
| `src/components/features/story-detail/EpisodeGeneratePanel.tsx` | Added canGenerate prop, readinessPanel slot, disabled state for generate button |
| `src/components/features/story-detail/index.ts` | Export StoryReadinessPanel |
| `src/components/features/index.ts` | Export StoryReadinessPanel |
| `src/hooks/useStoryDetail.ts` | Integrated useStoryReadiness hook, auto-check on panel open |
| `src/app/stories/[id]/page.tsx` | Added readiness state variables, passed to EpisodeGeneratePanel |

### API Endpoints Used

```
POST /api/v1/stories/{story_id}/readiness-check  - Check story readiness
POST /api/v1/stories/{story_id}/quick-fix        - Auto-fix missing fields
```

### UI Flow

1. User opens "Generate Episodes" panel on story detail page
2. Readiness check automatically runs, showing pass/fail status
3. Failed checks displayed with severity (CRITICAL/ERROR/WARNING/INFO)
4. Auto-fixable issues (synopsis, main_conflict, setting, world_building) show "Quick Fix" button
5. User can preview fixes (dry_run=true) before applying
6. After applying fixes, readiness refreshes and story data reloads
7. Generate button disabled if can_proceed=false (CRITICAL issues exist)

## Validation

### Frontend Lint
```bash
cd ai-pic-frontend && npm run lint
# 0 errors, 7 pre-existing warnings
```

### Backend Tests
```bash
cd ai-pic-backend && pytest tests/unit/services/readiness/ tests/integration/test_readiness_api.py -v
# 58 passed
```

## Next Steps

1. Chrome E2E verification: Test complete flow "story missing fields -> quick-fix -> generate episode"
2. Update tasks.md to mark frontend integration complete
3. Consider adding readiness check to episode workspace before script generation

## Linked Commits

- (pending commit)
