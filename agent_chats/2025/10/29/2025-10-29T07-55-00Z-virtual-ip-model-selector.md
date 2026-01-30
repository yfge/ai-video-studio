---
id: 2025-10-29T07-55-00Z-virtual-ip-model-selector
date: 2025-10-29T07:55:00Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [frontend, virtual-ip]
related_paths:
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
summary: "Adopted shared model selector for virtual IP image generation and simplified model fallback logic"
---

## User Prompt

先把所有模型选择／列表相关的组件统一化，并由后端统一提供，现在太乱了。

## Goals

- Reuse the shared model selector within the virtual IP image generator.
- Remove bespoke model state handling in favor of cached backend responses.
- Keep generation flows relying on backend defaults when the user does not choose a model.

## Changes

- Wired `virtual-ip/[id]/images/page.tsx` to the new `useAvailableModels` hook and `ModelSelector` component.
- Simplified generation fallback to use the backend-recommended model and refreshed helper text.
- Removed redundant model state bookkeeping and ensured task creation derives provider info from the unified list.

## Validation

- npm run lint

## Next Steps

- Consider extending the selector to virtual IP tasks/images for other asset types once backend scopes are available.

## Linked Commits

N/A
