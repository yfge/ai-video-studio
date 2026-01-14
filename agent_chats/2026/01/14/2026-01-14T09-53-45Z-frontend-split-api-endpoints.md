---
id: 2026-01-14T09-53-45Z-frontend-split-api-endpoints
date: 2026-01-14T09:53:45Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, refactor, api]
related_paths:
  - ai-pic-frontend/src/utils/api/endpoints/script.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/script/audio.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/script/core.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/script/generation.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/script/paths.ts
  - ai-pic-frontend/src/utils/api/endpoints/script/storyboard.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/story-structure.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/story-structure/beats.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/story-structure/environments.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/story-structure/scenes.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/story-structure/shots.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/story-structure/treatments.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/virtual-ip-image.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/virtual-ip-image/crud.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/virtual-ip-image/generation.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/virtual-ip-image/variants.endpoints.ts
summary: "Split oversized frontend API endpoint modules to comply with file-size limits while preserving exports."
---

## User Prompt
- 优化所有 provider 和域；选择不同 provider 时动态加载输入；原子化分布提交。

## Goals
- 将超长的 `src/utils/api/endpoints/*` 模块拆分为更小的文件，满足 TS 文件行数限制（≤250 行/文件）。
- 保持对外导出（函数名、`*API` namespace）不变，避免影响现有页面/调用方。

## Changes
- 将 `virtual-ip-image.endpoints.ts` 拆分为 `crud/generation/variants` 三个子模块，原文件改为薄聚合导出 + `virtualIPImageAPI` 组装。
- 将 `story-structure.endpoints.ts` 拆分为 `scenes/beats/shots/treatments/environments` 子模块，原文件改为薄聚合导出 + `storyStructureAPI` 组装。
- 将 `script.endpoints.ts` 拆分为 `core/generation/audio/storyboard` 子模块，并抽出 `paths.ts`；原文件改为薄聚合导出 + `scriptAPI` 组装。

## Validation
- `cd ai-pic-frontend && npm run lint`（仅 warnings，无 error）。
- `./docker/build_prod_images.sh`（success）。

## Next Steps
- 继续把文生图/图生图的 `generation_profile` / `seed` / `steps` / `cfg_scale` / `negative_prompt` / `strength` 等参数在各域的 API 调用中对齐，并做 provider-aware UI 动态输入。

## Linked Commits
- (pending)

