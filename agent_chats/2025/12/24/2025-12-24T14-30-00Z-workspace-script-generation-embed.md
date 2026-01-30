---
id: 2025-12-24T14-30-00Z-workspace-script-generation-embed
date: 2025-12-24T14:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, workspace, script-generation, no-navigation]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceScriptTabContent.tsx
summary: "Embed script generation form directly in workspace, eliminating navigation to old episode page"
---

## User Prompt

User reported: "http://localhost:8089/episodes/b199d0900c74487c84ba432fb5d4a932?action=generate-script 生成剧本跳到这里了"

User explicitly demanded: "一集剧所有 的操作都应该在这个页面完成！！！ http://localhost:8089/episodes/b199d0900c74487c84ba432fb5d4a932/workspace"

Translation: ALL operations for an episode must be completed in the workspace page - no redirects to other pages.

## Goals

1. Embed the script generation form directly in the workspace Script tab
2. Remove navigation redirect to old episode page for script generation
3. Call the script generation API directly from the workspace

## Changes

### Frontend

1. **`ai-pic-frontend/src/components/features/episode/WorkspaceScriptTabContent.tsx`**

   - Updated interface to accept script generation props:
     - `generateForm`, `setGenerateForm`
     - `formats`, `languages`
     - `useAsync`, `setUseAsync`
     - `promptPreview`, `setPromptPreview`
     - `generating`, `onGenerate`
   - When no script exists, shows `ScriptGenerationForm` directly instead of a button that navigates away
   - Form includes all options: format, language, dialogue style, scene detail, model selection, temperature, async mode

2. **`ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx`**
   - Added `scriptAPI` import
   - Extracted script generation state from `useEpisodeDetail`:
     - `formats`, `languages`, `generating`, `setGenerating`
     - `useAsync`, `setUseAsync`, `promptPreview`, `setPromptPreview`
     - `generateForm`, `setGenerateForm`, `setScripts`
   - Replaced navigation-based `handleGenerateScript` with direct API call:
     - Supports both sync and async script generation
     - Updates local script list on success
     - Shows appropriate alerts for success/failure
   - Updated `WorkspaceScriptTabContent` props to pass all generation state

## Validation

1. Frontend lint: `npm run lint` passes with no errors
2. Browser verification via Chrome DevTools MCP:
   - Navigated to `/episodes/b199d0900c74487c84ba432fb5d4a932/workspace?tab=script`
   - Script generation form is now embedded directly in the page
   - All form fields visible: format, language, dialogue style, scene detail, model, temperature, async checkbox
   - Clicked "开始生成" button
   - Alert appeared: "剧本生成任务已创建（task_id=392）"
   - **URL stayed at workspace page** - no navigation occurred
   - Verified Timeline tab still works with "一键生成全部" button

## Next Steps

1. Consider adding task progress polling to show script generation status
2. When script is generated, automatically refresh and show the script content
3. Consider adding a "regenerate" option for existing scripts in the workspace

## Linked Commits

- (pending commit)
