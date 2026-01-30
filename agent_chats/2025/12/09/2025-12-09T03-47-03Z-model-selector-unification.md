---
id: 2025-12-09T03-47-03Z-model-selector-unification
date: 2025-12-09T03:47:03Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, tasks, ai-models]
related_paths:
  - ai-pic-frontend/src/app/tasks/page.tsx
  - ai-pic-frontend/src/components/MultiModelSelector.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "Abstracted model selection into a reusable component and switched task creation to API-fetched models"
---

## User Prompt

把模型选择抽象成一个组件，全局使用；全局处理，模型都以API 拉到的模型为主

## Goals

- Remove hardcoded model lists and rely on backend-provided models
- Reuse a single component for model selection across pages
- Keep task creation payload carrying provider/model info from API data

## Changes

- Added `MultiModelSelector` component that fetches models via `/api/v1/ai/models/available`, groups by provider, supports multi-select, and shows selected chips
- Updated tasks page to use the new selector, drop static configs, and pass provider/model metadata into task creation payload
- Extended frontend API typings so task creation accepts dynamic model_id/model_name/count

## Validation

- `cd ai-pic-frontend && npm run lint`

## Next Steps

- If other pages need multi-model selection, switch them to `MultiModelSelector` for consistency
- Confirm backend task consumers respect the new model_id/model_name fields in parameters

## Linked Commits

- (pending)
