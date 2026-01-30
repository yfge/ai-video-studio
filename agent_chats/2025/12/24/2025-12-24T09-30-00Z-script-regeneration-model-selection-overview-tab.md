---
id: 2025-12-24T09-30-00Z-script-regeneration-model-selection-overview-tab
date: 2025-12-24T09:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, backend, script, workspace]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeWorkspaceHeader.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceScriptTabContent.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceOverviewTabContent.tsx
  - ai-pic-frontend/src/components/features/episode/index.ts
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/utils/api/endpoints/script.endpoints.ts
summary: "Add script regeneration with model selection and episode overview tab"
---

## User Prompt

1. "提供重新生成剧本的功能" (Add script regeneration feature)
2. "重新生成不能选择模型么？" (Add model selection to regeneration)
3. "在 剧本 时间轴 分镜 这一层级上 再加上一个剧集概要" (Add Episode Overview as first tab)

## Goals

1. Add script regeneration button to workspace script tab
2. Enable model selection when regenerating scripts
3. Add Episode Overview tab as first tab in workspace showing episode info from story generation

## Changes

### Backend Changes

**`ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`**:

- Added `ScriptRegenerateRequest` Pydantic model with optional `model` field
- Updated `regenerate_script` endpoint to accept optional model parameter
- Updated `regenerate_script_by_business_id` endpoint similarly
- Modified `_regenerate_script_instance` helper to accept `override_model` parameter

### Frontend Changes

**`ai-pic-frontend/src/utils/api.ts`**:

- Updated `regenerateScript` method to accept optional `{ model?: string }` options

**`ai-pic-frontend/src/utils/api/endpoints/script.endpoints.ts`**:

- Added `ScriptRegenerateRequest` interface

**`ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx`**:

- Added "overview" to TabKey type
- Changed default tab from "script" to "overview"
- Added regenerating state and handleRegenerateScript with model parameter
- Added WorkspaceOverviewTabContent component usage

**`ai-pic-frontend/src/components/features/episode/WorkspaceScriptTabContent.tsx`**:

- Added regeneration modal with ModelSelector component
- Added regenerateModel state management
- Updated onRegenerateScript prop to accept optional model parameter

**`ai-pic-frontend/src/components/features/episode/EpisodeWorkspaceHeader.tsx`**:

- Updated activeTab type to include "overview"
- Added "剧集概要" as first tab in navigation

**`ai-pic-frontend/src/components/features/episode/WorkspaceOverviewTabContent.tsx`** (NEW):

- Created new component to display episode overview
- Shows: 基本信息, 剧集概要, 剧情要点, 冲突点, 角色弧线, 标签, 元数据
- Proper parsing of plot_points and conflicts with timing/intensity display

**`ai-pic-frontend/src/components/features/episode/index.ts`**:

- Added export for WorkspaceOverviewTabContent

## Validation

1. Ran `npm run lint` - passed with only pre-existing warnings
2. Chrome DevTools MCP E2E testing:
   - Navigated to `/episodes/1e8ecf446e26403e94d8d0bcafb6ce26/workspace?tab=overview`
   - Verified Episode Overview tab displays correctly
   - Confirmed plot_points show timing labels (e.g., "开场 0:00-0:30")
   - Confirmed conflicts show intensity labels ("high", "medium")
   - All episode information properly displayed

## Next Steps

1. Enhance workflow steps with more prominent arrow indicators (user request)
2. Consider adding edit capability for episode overview fields
3. Test script regeneration with different models

## Linked Commits

- (to be added after commit)
