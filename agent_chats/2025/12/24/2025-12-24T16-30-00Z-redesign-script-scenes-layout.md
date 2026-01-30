---
id: 2025-12-24T16-30-00Z-redesign-script-scenes-layout
date: 2025-12-24T16:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, script-tab, ui-redesign, ux-improvement]
related_paths:
  - ai-pic-frontend/src/components/features/script/ScriptScenesTab.tsx
summary: "Redesign script scenes tab with left sidebar and detailed scene cards"
---

## User Prompt

User reported: "这个交互还是太丑了，1. 把场景列表放在左侧，然后要详细的显示每一个场景的信息"

Translation: The current interaction is too ugly. Put the scene list on the left side and show detailed information for each scene.

## Goals

1. Redesign scene list layout with left sidebar
2. Show more detailed scene information in each scene card
3. Improve overall visual design

## Changes

### Frontend

**`ai-pic-frontend/src/components/features/script/ScriptScenesTab.tsx`**

Complete rewrite with new layout:

1. **Left sidebar (320px width)**

   - Fixed header with "场景列表" title and scene count
   - Scrollable scene list
   - Scene cards show:
     - Scene number and time badge (night/dawn/etc)
     - Location with 📍 icon
     - Description preview (line-clamp-2)
     - Stats row: character count (👤) and dialogue count (💬)
   - Active scene has blue highlight with ring

2. **Right panel (flex-1)**

   - Large scene header with number and time badge
   - Location display
   - Description section with notes
   - Characters section with purple badges
   - Two-column grid for dialogues and stage directions
   - Structure info section (beats and shots)

3. **Layout improvements**
   - Full height flex layout (calc(100vh-320px))
   - Scrollable panels with overflow
   - Better visual hierarchy with rounded corners and shadows
   - Consistent spacing and typography

## Validation

1. Frontend lint: `npm run lint` - passes with only pre-existing warnings
2. Browser verification via Chrome DevTools MCP:
   - Navigated to `/episodes/b199d0900c74487c84ba432fb5d4a932/workspace?tab=script`
   - Verified left sidebar shows scene list with detailed cards
   - Each scene shows: number, time, location, description, character/dialogue counts
   - Right panel shows comprehensive scene details
   - Scrolling works correctly in both panels

## Next Steps

1. Consider adding scene thumbnails if available
2. Consider collapsible sections in the detail panel
3. Add keyboard navigation support

## Linked Commits

- 96beca4 feat(frontend): redesign script scenes tab with left sidebar layout
