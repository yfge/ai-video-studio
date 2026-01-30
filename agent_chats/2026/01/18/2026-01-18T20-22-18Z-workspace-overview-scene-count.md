---
id: 2026-01-18T20-22-18Z-workspace-overview-scene-count
date: 2026-01-18T20:22:18Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, episode, workspace]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceOverviewTabContent.tsx
summary: "工作台概览页展示所选剧本的真实场景数，避免误以为剧本不完整"
---

## User Prompt

`/episodes/.../workspace` 中剧本内容“扯淡/不及格”，需要定位问题并整体修复；要求原子化分布提交并做浏览器自测。

## Goals

- 概览页“场景数”与当前选中剧本一致，避免被 `episode.scene_count` 的滞后/不一致数据误导。
- 保持改动最小：不改变现有脚本结构渲染，只修正展示口径。

## Changes

- `WorkspaceOverviewTabContent` 增加可选入参 `scriptSceneCount`，用于覆盖展示口径。
- `EpisodeWorkspacePage` 从 `selectedScript.scenes.length` 计算 `scriptSceneCount` 并传入概览页。

## Validation

- Frontend lint: `cd ai-pic-frontend && npm run lint`
- Docker build: `./docker/build_prod_images.sh`
- Chrome E2E：
  - 登录后访问 `http://localhost:8089/episodes/1cca3cc61d7740b4b5f73bccf8fe4d32/workspace?tab=overview&scriptId=101`
  - 确认“场景数”显示为 `9`（与“剧本”tab 的场景列表一致），不再显示旧的 `episode.scene_count=1`。

## Next Steps

- 若确认 `episode.scene_count` 语义应等于“最新剧本场景数”，考虑在后端写入/更新该字段，避免多处口径分叉。
- 继续梳理 script/episode 生成质量问题（若仍“不及格”，优先从生成 prompt、约束与评审环节入手）。

## Linked Commits

- fix(frontend): show selected script scene count in workspace
