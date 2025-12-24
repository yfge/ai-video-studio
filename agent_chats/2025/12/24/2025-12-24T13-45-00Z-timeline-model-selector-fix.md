---
id: 2025-12-24T13-45-00Z-timeline-model-selector-fix
date: 2025-12-24T13:45:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, bug-fix, model-selection]
related_paths:
  - ai-pic-frontend/src/components/features/episode/AudioTimelineSection.tsx
summary: "Fix timeline model selector to use provider:model_id format"
---

## User Prompt

"这个页面的模型选择有问题 http://localhost:8089/episodes/xxx/workspace?tab=timeline 导致后面的调用一直在出错"

Error shown:
```
provider=openai model=deepseek-chat status=failure
```

## Goals

Fix the model selector on the timeline tab to send the correct `provider:model_id` format to the backend.

## Changes

### Frontend Changes

**`ai-pic-frontend/src/components/features/episode/AudioTimelineSection.tsx`**:
- Fixed model selector option values to use `provider:model_id` format
- Changed from using `model.id` (e.g., "deepseek-chat") to constructing the full model ID
- Code change (lines 316-325):
  ```tsx
  {availableModels.map((model) => {
    // Use provider:model_id format for backend routing
    const fullModelId = model.model_id || `${model.provider}:${model.id}`;
    return (
      <option key={fullModelId} value={fullModelId}>
        {model.name || model.id}
      </option>
    );
  })}
  ```

### Root Cause Analysis

The backend's `_resolve_prefer_provider_and_model()` in `ai_service_manager.py` expects model strings in `provider:model_id` format (e.g., "deepseek:deepseek-chat"). When just the model ID was sent (e.g., "deepseek-chat"), the backend couldn't determine the correct provider and defaulted to OpenAI, causing the error.

## Validation

1. Ran `npm run lint` - passed with only pre-existing warnings
2. Chrome DevTools MCP testing:
   - Navigated to timeline tab
   - Used JavaScript evaluation to verify option values
   - Confirmed values now show correct format:
     - `"deepseek:deepseek-chat"` (was: `"deepseek-chat"`)
     - `"google:gemini-2.0-flash"` (was: `"gemini-2.0-flash"`)

## Next Steps

1. Test actual timeline generation with a selected model to ensure backend receives correct format
2. Consider applying the same fix pattern to other model selectors in the codebase

## Linked Commits

- d612a70 fix(timeline): use provider:model_id format for model selector
- 2874a65 fix(frontend): resolve type errors for production build
