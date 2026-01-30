---
id: 2025-12-09T13-14-45Z-model-selector-providers
date: 2025-12-09T13:14:45Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, models]
related_paths:
  - ai-pic-frontend/src/app/stories/page.tsx
summary: "Allow story generator model dropdown to list all configured text providers"
---

## User Prompt

1. 现在已经配置了google,deepseek,火山引擎和openai 但是文生文的列表 只有openai的

## Goals

- Make the story generation model selector show all configured text providers instead of only OpenAI.
- Verify in the UI that multiple providers appear after the change.

## Changes

- Removed the hardcoded `filterModels` constraint in `ai-pic-frontend/src/app/stories/page.tsx` so the story model dropdown now includes every available text provider.

## Validation

- `npm run lint` (frontend) — passes with existing warnings from unrelated files (React hook deps in `MultiModelSelector.tsx`, unused import in `useAvailableModels.ts`).
- Chrome MCP E2E: http://localhost:8089/ → login (geyunfei / Gyf@845261) → 故事创作 → AI生成故事 form shows provider dropdown with DeepSeek / Google / OpenAI / 火山引擎 entries.

## Next Steps

- None.

## Linked Commits

- fix(frontend): show all story text providers
