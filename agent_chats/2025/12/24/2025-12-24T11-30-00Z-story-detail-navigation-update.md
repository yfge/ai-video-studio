---
id: 2025-12-24T11-30-00Z-story-detail-navigation-update
date: 2025-12-24T11:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, navigation, workflow, refactor]
related_paths:
  - ai-pic-frontend/src/hooks/useStoryDetail.ts
summary: "Update story detail navigation to use unified workspace"
---

## User Prompt

Continue Phase 4 of the episode workspace refactoring - update story detail page entry buttons to link to the unified workspace instead of old episode pages.

## Goals

1. Update `navigateToEpisode` to go to `/episodes/[id]/workspace`
2. Update `navigateToStoryboard` to go to `/episodes/[id]/workspace?tab=storyboard`
3. Ensure seamless transition from old URL pattern to new unified workspace

## Changes

### Modified Files

1. **`ai-pic-frontend/src/hooks/useStoryDetail.ts`** (lines 195-198)
   - Changed `navigateToEpisode` from `/episodes/${id}` to `/episodes/${id}/workspace`
   - Changed `navigateToStoryboard` from `/episodes/${id}/storyboard` to `/episodes/${id}/workspace?tab=storyboard`
   - Maintains backward compatibility - same function signatures, just new URLs

## Validation

Browser verification via Chrome DevTools MCP:

1. Navigated to story detail page: `/stories/6d7c528b4b064a5f99689f095f5bef90`
2. Clicked "查看" button on Episode 7:
   - Successfully navigated to `/episodes/ea5e2e64f93c48109a05f65c00d6e767/workspace`
   - Workspace loaded with workflow steps (剧本 ✓ → 时间轴 ○ → 分镜 ○)
   - Script tab active by default
3. Clicked "分镜管理" button on Episode 1:
   - Successfully navigated to `/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=storyboard`
   - Storyboard tab active, showing "暂无分镜" content

All navigation paths verified working correctly.

## Next Steps

1. Consider adding redirects from old URLs to new workspace URLs (Phase 5 in plan)
2. Update any remaining hardcoded links to old episode URLs
3. Continue with Phase 3 of the plan (refactoring the 3283-line storyboard page)

## Linked Commits

- 31bf7b3 feat(frontend): update story detail navigation to workspace
