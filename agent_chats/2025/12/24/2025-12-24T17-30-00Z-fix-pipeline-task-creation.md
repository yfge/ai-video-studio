---
id: 2025-12-24T17-30-00Z-fix-pipeline-task-creation
date: 2025-12-24T17:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, bugfix, api, timeline-tab]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
summary: "Fix pipeline task creation error by adding missing API method"
---

## User Prompt

User reported error "操作失败 创建一键流水线任务失败" when clicking the "一键生成全部" button on the timeline tab.

## Goals

1. Identify root cause of pipeline task creation failure
2. Fix the API method availability issue
3. Verify the fix works in browser

## Changes

### Frontend

**`ai-pic-frontend/src/utils/api.ts`**

Root cause: Module resolution conflict between legacy `api.ts` and new modular `api/endpoints/` structure. The import `@/utils/api` resolved to the legacy file, which was missing `generateTimelinePipelineAsync` method.

Added missing method to ApiClient class (after line 1918):
```typescript
async generateTimelinePipelineAsync(
  scriptId: number | string,
  payload?: {
    tts_model?: string;
    timing_model?: string;
    overwrite_audio?: boolean;
    overwrite_timeline?: boolean;
    overwrite_storyboard?: boolean;
    min_pause_seconds?: number;
  },
) {
  return this.request<{ task_id: number; status: string }>(
    this.scriptPath(scriptId, "/timeline-pipeline/generate-async"),
    {
      method: "POST",
      body: JSON.stringify(payload || {}),
    },
  );
}
```

Added method binding to scriptAPI export (after line 2400):
```typescript
generateTimelinePipelineAsync:
  apiClient.generateTimelinePipelineAsync.bind(apiClient),
```

## Validation

1. Frontend lint: `npm run lint` - passes with only pre-existing warnings
2. Browser verification via Chrome DevTools MCP:
   - Logged in as test user
   - Navigated to `/episodes/b199d0900c74487c84ba432fb5d4a932/workspace?tab=timeline`
   - Clicked "一键生成全部" button
   - Result: Task created successfully (task_id=394)
   - UI shows: "一键流水线任务已创建（task_id=394）"

## Next Steps

1. Consider consolidating legacy and modular API exports to avoid future conflicts
2. Monitor task completion for the created pipeline task

## Linked Commits

- bc01d99 fix(frontend): add generateTimelinePipelineAsync to legacy scriptAPI
