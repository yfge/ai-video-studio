---
id: 2025-12-19T10-26-13Z-script-page-link-fix
date: 2025-12-19T10:26:19Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, routing]
related_paths:
  - ai-pic-frontend/src/components/features/story-detail/EpisodeListSection.tsx
  - ai-pic-frontend/src/hooks/useScriptDetail.ts
  - ai-pic-frontend/src/hooks/useStoryDetail.ts
summary: "Use script business IDs in story navigation and remove read-only warning"
---

## User Prompt
- `http://localhost:8089/scripts/30` 页面没有修正。
- 去掉“场景结构为只读模式，需要管理员权限编辑”的提醒。

## Goals
- 从故事详情进入剧本页时优先使用业务 UUID。
- 移除场景结构只读提示。

## Changes
- Updated story detail navigation to push `script.business_id` with numeric fallback.
- Removed the read-only warning toast from the script detail hook.

## Validation
- `npm run lint` (ai-pic-frontend).
- `./docker/build_prod_images.sh` succeeded (tag `1d629e7`).
- Chrome MCP: opened `http://localhost:8089/stories/23`, clicked the latest script "查看", landed on `http://localhost:8089/scripts/3ad12f9a82424140a69442697bd104d5`; verified `document.body.innerText` does not include the read-only warning text.

## Next Steps
- None.

## Linked Commits
- Pending
