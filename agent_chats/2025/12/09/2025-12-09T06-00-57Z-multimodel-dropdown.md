---
id: 2025-12-09T06-00-57Z-multimodel-dropdown
date: 2025-12-09T06:00:57Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, ui, ai-models]
related_paths:
  - ai-pic-frontend/src/components/MultiModelSelector.tsx
summary: "Add provider/model dual dropdown when single-select to avoid overflow"
---

## User Prompt

重构前端 的模型选择控件，做成 供应商/模型的两级下拉菜单，现在已经显示不下了。

## Goals

- Prevent model chip overflow by using provider + model dropdowns when single-select.
- Keep multi-select chip UX unchanged.

## Changes

- `MultiModelSelector` now renders provider and model dropdowns when `multiple=false`; auto option preserved; switching provider clears incompatible selections.
- Multi-select mode still uses provider-grouped chips. Provider inference honors current value/default.

## Validation

- `npm run lint` (pass).

## Next Steps

- Apply the dropdown UX to other single-select usages if needed.

## Linked Commits

- (this commit)
