---
id: 2026-02-02T10-15-00Z-fix-legacy-api-readiness
date: 2026-02-02T10:15:00Z
participants: [human, claude-opus-4-5]
models: [claude-opus-4-5-20251101]
tags: [frontend, bugfix, api, readiness-check]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
summary: "Fixed storyAPI.checkStoryReadiness is not a function error by adding methods to legacy api.ts"
---

## User Prompt

Continue from previous conversation - fix the runtime error where `storyAPI.checkStoryReadiness is not a function`.

## Goals

1. Add readiness check and quick-fix methods to legacy api.ts for backward compatibility
2. Ensure the frontend can call readiness APIs through the existing storyAPI export

## Changes

### Modified Files

| File | Change |
|------|--------|
| `ai-pic-frontend/src/utils/api.ts` | Added checkStoryReadiness, checkEpisodeReadiness, quickFixStory methods to apiClient class and storyAPI export |

### Methods Added

```typescript
// In apiClient class
async checkStoryReadiness(storyIdOrBiz: number | string)
async checkEpisodeReadiness(storyIdOrBiz: number | string, episodeIdOrBiz: number | string)
async quickFixStory(storyIdOrBiz: number | string, request?: { dry_run?: boolean })

// In storyAPI export
checkStoryReadiness: (id) => apiClient.checkStoryReadiness(id)
checkEpisodeReadiness: (storyId, episodeId) => apiClient.checkEpisodeReadiness(storyId, episodeId)
quickFixStory: (id, request) => apiClient.quickFixStory(id, request)
```

## Validation

### Frontend Lint
```bash
cd ai-pic-frontend && npm run lint
# 0 errors, 7 pre-existing warnings
```

## Next Steps

1. Chrome E2E verification: Test complete flow "story missing fields -> quick-fix -> generate episode"
2. Update tasks.md to mark frontend integration complete

## Linked Commits

- (pending)
