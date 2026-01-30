---
id: 2025-12-26T12-00-00Z-duration-control-frontend-integration
date: 2025-12-26T12:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, duration-control, timeline-pipeline, ui]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/utils/api/endpoints/script.endpoints.ts
  - ai-pic-frontend/src/components/features/episode/WorkspaceTimelineTabContent.tsx
  - ai-pic-frontend/src/components/features/episode/AudioTimelineSection.tsx
summary: "Added use_duration_control parameter to frontend API and UI toggle for Duration Orchestrator"
---

## User Prompt

Continue the duration control integration by adding the `use_duration_control` parameter to the frontend API types and adding a UI toggle for enabling Duration Orchestrator in the timeline pipeline.

## Goals

1. Add `use_duration_control` to frontend API type definitions
2. Add toggle switch in the timeline tab UI
3. Pass the parameter through to the backend API call
4. Validate E2E that the toggle is visible and functional

## Changes

### 1. API Type Definitions

**`ai-pic-frontend/src/utils/api.ts` (line 1931)**:

```typescript
async generateTimelinePipelineAsync(
  scriptId: number | string,
  payload?: {
    // ... existing fields ...
    use_duration_control?: boolean;  // NEW
  },
)
```

**`ai-pic-frontend/src/utils/api/endpoints/script.endpoints.ts` (line 250)**:

```typescript
export async function generateTimelinePipelineAsync(
  scriptId: number | string,
  payload?: {
    // ... existing fields ...
    use_duration_control?: boolean; // NEW
  },
);
```

### 2. State Management in WorkspaceTimelineTabContent.tsx

Added state hook and passed to API call:

```typescript
const [useDurationControl, setUseDurationControl] = useState(false);

// In API call:
use_duration_control: useDurationControl,

// Dependencies updated:
}, [selectedScriptId, timingModel, useDurationControl, showAlert]);
```

### 3. UI Toggle in AudioTimelineSection.tsx

Added props interface:

```typescript
// Duration control
useDurationControl: boolean;
setUseDurationControl: (value: boolean) => void;
```

Added checkbox toggle near model selector:

```tsx
<label
  className="flex items-center gap-2 cursor-pointer"
  title="启用 Duration Orchestrator 确保时长在目标的±10%范围内"
>
  <input
    type="checkbox"
    checked={useDurationControl}
    onChange={(e) => setUseDurationControl(e.target.checked)}
    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
  />
  <span className={useDurationControl ? "text-blue-600 font-medium" : ""}>
    时长精控
  </span>
  {useDurationControl && <span className="text-xs text-blue-500">(±10%)</span>}
</label>
```

## Validation

1. **Lint Check**: `npm run lint` passed successfully
2. **Chrome E2E Test**:
   - Navigated to `http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=timeline`
   - Hard refresh with cache bypass
   - Confirmed "时长精控" checkbox visible (uid=12_408)
   - UI shows correctly with model dropdown and duration control toggle side by side
3. **Current Timeline Data**:
   - Timeline duration: 118.0s (actual) vs 180s (target) = 65.5%
   - With Duration Orchestrator enabled, future generations should hit ±10% of target

## Next Steps

1. Backend already supports `use_duration_control` in `TimelinePipelineGenerateRequest`
2. When user enables toggle and clicks "一键生成全部", Duration Orchestrator will:
   - Allocate budget across scenes proportionally
   - Generate TTS with target duration constraints
   - Use REACT validation mechanism to correct timing issues
3. Consider adding similar toggle to episode regeneration flow

## Linked Commits

- (pending) feat(frontend): add duration control toggle to timeline pipeline UI
