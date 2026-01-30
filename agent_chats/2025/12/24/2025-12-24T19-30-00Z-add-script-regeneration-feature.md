---
id: 2025-12-24T19-30-00Z-add-script-regeneration-feature
date: 2025-12-24T19:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, workspace, script-regeneration]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceScriptTabContent.tsx
summary: "Add script regeneration button to workspace script tab"
---

## User Prompt

User requested: "提供重新生成剧本的功能" (Provide script regeneration feature)

## Goals

1. Add a "重新生成剧本" (Regenerate Script) button to the workspace script tab
2. Wire up the regeneration handler to call the existing backend API
3. Allow users to regenerate scripts to apply the new review classification step

## Changes

### Frontend

**`ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx`**

- Added `regenerating` state to track regeneration in progress
- Added `handleRegenerateScript` callback that:
  - Calls `scriptAPI.regenerateScript(scriptId)`
  - Updates the script list with regenerated content
  - Shows success/error alert messages
- Passed `onRegenerateScript` and `regenerating` props to `WorkspaceScriptTabContent`

**`ai-pic-frontend/src/components/features/episode/WorkspaceScriptTabContent.tsx`**

- Added `onRegenerateScript` and `regenerating` optional props to interface
- Added regeneration button with:
  - Amber color scheme to distinguish from other actions
  - Spinning loader during regeneration
  - Disabled state while regenerating
  - Refresh icon when idle
- Positioned button in header row alongside sub-tab navigation

## Validation

1. Lint check: `npm run lint` passes (only pre-existing warnings)
2. Chrome DevTools MCP E2E test:
   - Navigated to `/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=script`
   - Verified "重新生成剧本" button appears
   - Clicked button, confirmed loading state with "重新生成中..."
   - Waited ~90 seconds for API call to complete
   - Received success message: "剧本重新生成成功"
   - Verified Scene 2 now shows "💬 2 对白" (was 0 before)
   - Confirmed dialogue classification is now correct

### Before/After Comparison (Scene 2)

| Metric           | Before | After |
| ---------------- | ------ | ----- |
| Dialogues        | 0      | 2 ✅  |
| Stage Directions | 5      | 4 ✅  |

The review step in the script agent correctly reclassified the two misclassified dialogues.

## Next Steps

1. Consider adding async regeneration option for large scripts
2. Monitor regeneration performance and add timeout handling if needed

## Linked Commits

- 057ba54 feat(frontend): add script regeneration button to workspace
