---
id: 2025-10-29T07-32-00Z-frontend-alert-modal-rollout
date: 2025-10-29T07:32:00Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [frontend, ui]
related_paths:
  - ai-pic-frontend/src/app/tasks/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
summary: "Replaced confirm dialogs and legacy `<img>` usage in task and virtual IP flows with the alert modal provider and Next Image"
---

## User Prompt

把所有的 alert/confirm 改成 modal 组件，并在 localhost:3000 覆盖故事→分镜链路；修复 lint 提示。

## Goals

- Move ad-hoc confirm dialogs in task and virtual IP pages onto `AlertModalProvider`.
- Standardize image rendering on Next.js `Image` to resolve lint and performance warnings.
- Keep task/virtual IP interactions typed and ID-safe after the modal refactor.

## Changes

- Updated `tasks/page.tsx` to confirm deletions through the alert modal and tightened ID guards.
- Refactored virtual IP list/detail/images pages to use modal confirmations, typed API loaders, and `next/image` for previews.
- Simplified data loaders with `useCallback` and consistent default model handling for image generation.

## Validation

- npm run lint

## Next Steps

- Align admin modals with shared API types to remove leftover local interfaces.
- Consider adding toast feedback when task refreshes populate new entries.

## Linked Commits

N/A
