---
id: 2025-12-26T12-30-00Z-script-selector-page-level
date: 2025-12-26T12:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, episode-workspace, ui]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/components/features/episode/AudioTimelineSection.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceTimelineTabContent.tsx
summary: "Move script selector from timeline tab to page level"
---

## User Prompt

User requested: "在这http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=timeline 个里面有一个剧本的列表，把这个列表直接提到页面级别吧"

Translation: "Move the script list from the timeline tab to the page level"

## Goals

1. Move script selector from inside the timeline tab content to page level
2. Make script selector visible across all tabs (overview, script, timeline, storyboard)
3. Remove duplicate script selector from AudioTimelineSection

## Changes

### workspace/page.tsx

Added script selector section between header and tab content:

```tsx
{
  /* Script Selector - Page Level */
}
{
  scripts && scripts.length > 0 && (
    <div className="mt-4 bg-white rounded-lg shadow p-4">
      <div className="flex items-center gap-4">
        <label>当前剧本</label>
        <select value={selectedScriptId}>...</select>
        <span>共 {scripts.length} 个剧本</span>
      </div>
    </div>
  );
}
```

Also added logic to avoid duplicate version display when title already contains version.

### AudioTimelineSection.tsx

- Removed `scripts` and `onSelectScript` props from interface
- Removed the duplicate script selector UI
- Simplified the grid layout

### WorkspaceTimelineTabContent.tsx

- Removed `onSelectScript` from interface
- Removed `onSelectScript` prop from function parameters
- Removed passing `onSelectScript` to AudioTimelineSection

### storyboard/page.tsx

- Enhanced existing script selector with version display
- Added script count badge
- Added logic to avoid duplicate version display
- Styled consistently with workspace page selector

## Validation

1. Lint check: No errors for modified files
2. Browser verification: Script selector now appears at page level
3. Multiple scripts visible: Shows v1.0 (ID 26) and v1.1 (ID 45)

## Next Steps

1. Verify script switching works correctly across all tabs
2. Consider adding script metadata display (scenes count, dialogues count)

## Linked Commits

- f854fdc feat(frontend): move script selector to page level in episode workspace
- deda868 feat(frontend): enhance storyboard page script selector
