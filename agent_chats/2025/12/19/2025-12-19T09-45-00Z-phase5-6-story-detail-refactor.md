---
id: 2025-12-19T09-45-00Z-phase5-6-story-detail-refactor
date: 2025-12-19T09:45:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, refactor, phase5]
related_paths:
  - ai-pic-frontend/src/app/stories/[id]/page.tsx
  - ai-pic-frontend/src/hooks/useStoryDetail.ts
  - ai-pic-frontend/src/components/features/story-detail/StoryDetailHeader.tsx
  - ai-pic-frontend/src/components/features/story-detail/StorySummarySection.tsx
  - ai-pic-frontend/src/components/features/story-detail/CharactersSection.tsx
  - ai-pic-frontend/src/components/features/story-detail/AdditionalInfoSection.tsx
  - ai-pic-frontend/src/components/features/story-detail/EpisodeGeneratePanel.tsx
  - ai-pic-frontend/src/components/features/story-detail/EpisodeListSection.tsx
  - ai-pic-frontend/src/components/features/story-detail/index.ts
  - ai-pic-frontend/src/components/features/index.ts
summary: "Phase 5.6: Refactored stories/[id]/page.tsx from 606 to 112 lines (82% reduction)"
---

## User Prompt

Continue Phase 5 frontend page refactoring. Task 5.6: Refactor stories/[id]/page.tsx (606 lines).

## Goals

1. Extract state management logic to custom hook `useStoryDetail`
2. Create modular UI components for story detail page
3. Reduce page.tsx to under 200 lines
4. Maintain all existing functionality including episode generation and display

## Changes

### Created Files

1. **`src/hooks/useStoryDetail.ts`** (231 lines)
   - Exported types: EpisodeGenForm, UseStoryDetailOptions
   - Exported utilities: extractEpisodeScenes, getEpisodeSceneCount
   - Core state: story, episodes, scriptsByEpisode, loading
   - Episode generation state: genOpen, genForm, promptPreview, useAsync, vips, focusCharacters
   - Event handlers: handlePreviewPrompt, handleGenerateEpisodes, toggleFocusCharacter
   - Navigation helpers: navigateToStories, navigateToEpisode, navigateToStoryboard, navigateToScript

2. **`src/components/features/story-detail/StoryDetailHeader.tsx`** (41 lines)
   - Story title, genre/theme badges, creation date
   - Back to list button

3. **`src/components/features/story-detail/StorySummarySection.tsx`** (64 lines)
   - Synopsis, conflict, resolution
   - Time/location settings, world building
   - Collapsible generation prompt viewer

4. **`src/components/features/story-detail/CharactersSection.tsx`** (84 lines)
   - Main characters list with roles, traits, arcs
   - Character relationships display
   - Conditional rendering if no data

5. **`src/components/features/story-detail/AdditionalInfoSection.tsx`** (87 lines)
   - Plot structure (Act 1/2/3)
   - Core values, visual style
   - Selling points list
   - Conditional rendering if no data

6. **`src/components/features/story-detail/EpisodeGeneratePanel.tsx`** (226 lines)
   - Collapsible panel with form fields
   - Episode count, duration, complexity, pacing
   - Model selector, temperature slider
   - Focus character selection
   - Async toggle, preview and generate buttons

7. **`src/components/features/story-detail/EpisodeListSection.tsx`** (303 lines)
   - Combines episode data with outline data
   - EpisodeCard sub-component with beats, scenes, scripts preview
   - BeatsPreview, ScenesPreview, ScriptsPreview helper components
   - Navigation to episode, storyboard, script pages

8. **`src/components/features/story-detail/index.ts`** (6 lines)
   - Barrel export for all story-detail components

### Modified Files

1. **`src/app/stories/[id]/page.tsx`** (606 → 112 lines, 82% reduction)
   - Now uses `useStoryDetail` hook for all state
   - Imports components from `@/components/features`
   - Clean component composition with loading/error states

2. **`src/components/features/index.ts`**
   - Added exports for all story-detail components

## Validation

- `npm run lint`: ✔ No ESLint warnings or errors
- All functionality preserved:
  - Story overview with synopsis, settings, world building
  - Character display with roles and relationships
  - Additional info (plot structure, core values, selling points)
  - Episode generation form with all options
  - Combined episode list with outlines and scripts
  - Navigation to episode, storyboard, and script pages

## Next Steps

1. Phase 5 is now complete - all 6 major pages have been refactored
2. Consider further splitting EpisodeListSection.tsx (303 lines) in future passes
3. Proceed to Phase 6 or other refactoring tasks as directed

## Linked Commits

- (pending commit for this change)
