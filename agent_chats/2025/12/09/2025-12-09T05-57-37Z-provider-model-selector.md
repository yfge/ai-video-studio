---
id: 2025-12-09T05-57-37Z-provider-model-selector
date: 2025-12-09T05:57:37Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, ui, ai-models]
related_paths:
  - ai-pic-frontend/src/components/ModelSelector.tsx
summary: "Refactor model selector into provider/model two-level dropdown"
---

## User Prompt

重构前端 的模型选择控件，做成 供应商/模型的两级下拉菜单，现在已经显示不下了。

## Goals

- Update the frontend model selector to handle many models by splitting provider and model selection.
- Preserve auto/default behaviors and loading/error states.

## Changes

- `ModelSelector` now renders two dropdowns: first selects provider (all/providers), second lists models under the chosen provider; auto option retained. Provider inference considers current value/defaultModel and resets invalid selections.
- Keeps filtering, helper text, auto-select default, and refresh behaviors intact.

## Validation

- `npm run lint` (pass).

## Next Steps

- Consider similar provider filtering for `MultiModelSelector` chip UI if multi-select lists grow further.

## Linked Commits

- (this commit)
