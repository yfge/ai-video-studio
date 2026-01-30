---
id: 2025-12-24T10-30-00Z-episode-workspace-page
date: 2025-12-24T10:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, episode, workspace, refactor]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeWorkspaceHeader.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeWorkflowSteps.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeHeader.tsx
  - ai-pic-frontend/src/hooks/useAvailableModels.ts
  - ai-pic-frontend/src/utils/api/types/ai-model.types.ts
summary: "Created unified episode workspace page with workflow steps visualization"
---

## User Prompt

Continue refactoring episode-related pages into a unified workspace with a strong workflow pattern (Script-Timeline-Storyboard). Create unified workspace page and fix browser verification issues.

## Goals

1. Create unified workspace page at `/episodes/[id]/workspace`
2. Create EpisodeWorkspaceHeader component with workflow status visualization
3. Create EpisodeWorkflowSteps component for step-by-step progress display
4. Fix API call issues where episodeKey was undefined
5. Browser-verify the complete workspace flow

## Changes

### New Files Created

1. **`ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx`** (~275 lines)

   - Unified workspace page with tab navigation (Script | Timeline | Storyboard)
   - URL-synced tab state via query parameter `?tab=`
   - Workflow status calculation based on episode/script metadata
   - Tab content components for each workflow step

2. **`ai-pic-frontend/src/components/features/episode/EpisodeWorkspaceHeader.tsx`** (~138 lines)

   - Unified header displaying episode info and workflow progress
   - Compact workflow indicator (top-right corner)
   - Full workflow steps section with action buttons
   - Tab navigation bar

3. **`ai-pic-frontend/src/components/features/episode/EpisodeWorkflowSteps.tsx`** (~100 lines)
   - Workflow step visualization component
   - Supports compact mode (status indicators) and full mode (cards with actions)
   - Color-coded steps (blue/indigo/purple) for visual distinction
   - Status icons: checkmark (ready), circle (pending), pulsing dot (generating)

### Bug Fixes

4. **`ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx`**

   - Fixed: `params.id as string` → `params?.id?.toString() || ""` (safe params handling)
   - Fixed: Wrong hook signature `useEpisodeDetail(episodeKey, () => {})` → `useEpisodeDetail({ episodeKey, showAlert })`
   - Fixed: Added missing `useAlertModal` import and usage
   - Fixed: Removed non-existent `error` destructuring from hook result

5. **`ai-pic-frontend/src/hooks/useAvailableModels.ts`**

   - Added deduplication logic for models using `model_id || id` as key
   - Prevents duplicate entries in model dropdown selectors

6. **`ai-pic-frontend/src/utils/api/types/ai-model.types.ts`**

   - Added optional `model_id?: string` field to AIModel interface
   - Supports backend-enriched model IDs like "provider:id"

7. **`ai-pic-frontend/src/components/features/episode/EpisodeHeader.tsx`**
   - Removed debug code showing `scene_count` (lines 21-22)

## Validation

Browser verification via Chrome DevTools MCP:

1. Navigated to `http://localhost:8089/episodes/ea5e2e64f93c48109a05f65c00d6e767/workspace`
2. Verified page loads correctly with episode title "第7集: 专属程序"盖世"上线"
3. Verified workflow steps display correctly:
   - Script: checkmark (ready)
   - Timeline: circle (pending)
   - Storyboard: circle (pending)
4. Verified API calls use correct episode ID (not `undefined`):
   - `GET /api/v1/episodes/business/ea5e2e64f93c48109a05f65c00d6e767` → 200
   - `GET /api/v1/scripts/episode/business/ea5e2e64f93c48109a05f65c00d6e767` → 200
5. Tested tab switching:
   - Script tab → Timeline tab → Storyboard tab
   - URL updates correctly with `?tab=` parameter
   - Content changes appropriately for each tab
6. Lint validation: `npm run lint` passes with no errors

## Next Steps

1. Phase 4: Update story detail page entry buttons to link to workspace
2. Set up route redirects from old URLs to workspace
3. Consider enhancing tab content with richer functionality in future phases

## Linked Commits

- (pending commit)
