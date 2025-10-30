---
id: 2025-10-29T07-50-00Z-model-selector-unification
date: 2025-10-29T07:50:00Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [frontend, ui]
related_paths:
  - ai-pic-frontend/src/hooks/useAvailableModels.ts
  - ai-pic-frontend/src/components/ModelSelector.tsx
  - ai-pic-frontend/src/app/stories/page.tsx
  - ai-pic-frontend/src/app/stories/[id]/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
summary: "Introduced a shared model selector hook/component and updated story/episode/script flows to rely on backend-provided model lists"
---

## User Prompt
先把所有模型选择／列表相关的组件统一化，并由后端统一提供，现在太乱了。

## Goals
- Expose a reusable hook for fetching/caching available models from the backend.
- Provide a consistent `ModelSelector` component with auto/default handling.
- Adopt the shared selector across story, episode, storyboard, and script pages.

## Changes
- Added `useAvailableModels` hook and `ModelSelector` component to centralize model fetching and rendering logic.
- Updated story list/detail, episode detail/storyboard, and script detail pages to drop ad-hoc model state in favor of the shared selector.
- Removed redundant `aiAPI.getAvailableModels` calls now covered by the shared hook/cache.

## Validation
- npm run lint

## Next Steps
- Replace remaining bespoke selectors (e.g. virtual IP image generator) with the shared component.

## Linked Commits
N/A
