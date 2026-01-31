---
id: 2026-01-31T10-45-00Z-frame-duration-splitter-frontend
date: 2026-01-31T10:45:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, storyboard, video-duration-alignment]
related_paths:
  - ai-pic-frontend/src/utils/api/types/video.types.ts
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - tasks.md
summary: "Added frontend UI for split/merged frame badges and duration adjustment audit"
---

## User Prompt

继续 (Continue implementing frontend changes for Phase 2)

## Goals

1. Update TypeScript types for split/merge frame metadata
2. Add UI badges for split frames ("第 2/3 段")
3. Add UI badges for merged frames ("合并自 N 个 beat")
4. Display duration_adjustment audit statistics
5. Show beat_range and parent_frame_id for split frames

## Changes

### 1. `src/utils/api/types/video.types.ts`

Added new fields to `StoryboardFrame` type:
```typescript
// Split frame linkage (from frame_duration_splitter)
parent_frame_id?: string;
split_index?: number;
total_splits?: number;
beat_range?: string;
// Merged frame linkage
merged_beat_ids?: string[];
```

Added new type `DurationAdjustmentAudit`:
```typescript
export type DurationAdjustmentAudit = {
  frame_count?: number;
  splits_performed?: number;
  merges_performed?: number;
  audit_notes?: string[];
};
```

Added `duration_adjustment` field to `StoryboardMeta`:
```typescript
duration_adjustment?: DurationAdjustmentAudit;
```

### 2. `src/app/episodes/[id]/storyboard/page.tsx`

**Frame card header badges:**
- Blue badge for split frames: "第 X/Y 段" with tooltip showing parent_frame_id and beat_range
- Amber badge for merged frames: "合并自 N 个 beat" with tooltip showing merged beat IDs

**Beat range display:**
- For split frames, shows "原始 beat 范围: XXXms" with truncated parent_frame_id

**Duration adjustment audit:**
- In storyboard meta section, shows "时长调整: 拆分 X 次、合并 Y 次"
- Tooltip shows audit_notes from the backend

## Validation

```bash
cd ai-pic-frontend && npm run lint
# Result: 0 errors, 7 warnings (pre-existing, unrelated to changes)
```

## Next Steps

1. E2E verification: Navigate to storyboard page with split/merged frames
2. Verify badges display correctly for split frames
3. Verify duration_adjustment audit shows in meta section

## Linked Commits

(To be committed)
