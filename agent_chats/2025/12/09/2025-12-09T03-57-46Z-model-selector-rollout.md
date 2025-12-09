---
id: 2025-12-09T03-57-46Z-model-selector-rollout
date: 2025-12-09T03:57:46Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, ai-models, ui]
related_paths:
  - ai-pic-frontend/src/components/MultiModelSelector.tsx
  - ai-pic-frontend/src/app/stories/page.tsx
  - ai-pic-frontend/src/app/stories/[id]/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
  - ai-pic-frontend/src/app/environments/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
summary: "Rolled MultiModelSelector across all model pickers with single-select support and API-driven data"
---
## User Prompt
替换所有 的模型选择部分！！

## Goals
- Replace all model selection UI with the shared API-driven selector
- Ensure single-select flows still work while using backend model lists
- Keep UX stable (auto/default selection preserved where applicable)

## Changes
- Extended `MultiModelSelector` with single-select support, auto/default handling, fetcher passthrough, and optional auto choice for “empty”
- Replaced every `ModelSelector` usage (stories, story details, episodes, storyboards, scripts, environments, virtual IP images) with `MultiModelSelector` in single-select mode, mapping state to/from string values
- Preserved helper texts and default model auto-fill logic in virtual IP images

## Validation
- `cd ai-pic-frontend && npm run lint`
- Chrome MCP: visited `/tasks` post-login; selector still renders grouped models from API without errors (other pages not re-tested in browser)

## Next Steps
- Consider deprecating the old `ModelSelector` component and cleaning it up if no longer referenced
- Run through key flows (stories/episodes/storyboard/script/env) in the UI to ensure single-select mapping works end-to-end

## Linked Commits
- (pending)
