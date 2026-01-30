---
id: 2025-10-29T07-38-00Z-gallery-image-optimisation
date: 2025-10-29T07:38:00Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [frontend, ui]
related_paths:
  - ai-pic-frontend/src/app/gallery/page.tsx
  - ai-pic-frontend/src/components/AIGenerationProcess.tsx
  - ai-pic-frontend/src/components/SmartInputField.tsx
summary: "Adopted Next Image and hook cleanups across gallery and shared generation components"
---

## User Prompt

把所有的 alert 都改成 modal 组件，并修复 lint 的 `<img>` 警告。

## Goals

- Replace raw `<img>` tags in the gallery modal with `next/image`.
- Remove unused React hooks and tidy generation workflows to quiet lint.
- Ensure AI generation modals respect dependency arrays and escaped strings.

## Changes

- Converted gallery grid and modal previews to `Image` and dropped unused image state.
- Updated `AIGenerationProcess` to use `useCallback` for generation start and escaped display strings.
- Trimmed unused imports in `SmartInputField` after switching to modal confirmations elsewhere.

## Validation

- npm run lint

## Next Steps

- Review admin-facing modals to align with shared types and modal provider patterns.

## Linked Commits

N/A
