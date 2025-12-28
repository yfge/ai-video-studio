---
id: 2025-12-28T07-55-47Z-storyboard-return-to-workspace
date: 2025-12-28T07:55:47Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, navigation, storyboard, workspace]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardTabContent.tsx
summary: "Ensure storyboard management returns to episode workspace storyboard tab and preserves scriptId."
---

## User Prompt
去掉 `http://localhost:8089/episodes/<episode_business_id>` 这个页面入口；从“分镜管理”返回剧集时，应返回到 `.../workspace?tab=storyboard&scriptId=58`。

## Goals
- “分镜管理”页的“返回剧集/返回剧集页”不再跳转到 `/episodes/<id>`，而是回到 workspace 的 storyboard tab，并带上当前 scriptId。
- 从 workspace 的 storyboard tab 进入“完整编辑器”时，URL 需要携带 scriptId，确保编辑与返回一致。

## Changes
- `episodes/[id]/storyboard`：
  - 统一“返回剧集/返回剧集页/未找到剧集”按钮，跳转到 `/episodes/<id>/workspace?tab=storyboard&scriptId=<activeScriptId>`。
- `WorkspaceStoryboardTabContent`：
  - “打开完整编辑器 →” 跳转到 `/episodes/<id>/storyboard?scriptId=<selectedScriptId>`，避免丢失当前剧本上下文。

## Validation
- Frontend lint：`cd ai-pic-frontend && npm run lint`（通过，既有 warnings 未升级为 error）。
- Docker 生产镜像构建：`./docker/build_prod_images.sh`（成功）。
- Chrome E2E（MCP/DevTools）：
  - 打开：`http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/storyboard?scriptId=58`
  - 点击“返回剧集” → URL 变为：`http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=storyboard&scriptId=58`
  - 在 workspace 分镜页点击“打开完整编辑器 →” → URL 回到：`http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/storyboard?scriptId=58`

## Next Steps
- 若需要彻底禁用 `/episodes/<id>` 页面，可考虑将其改为 server redirect 到 `/episodes/<id>/workspace`（并保留 search params）。

## Linked Commits
- fix(frontend): return storyboard to workspace tab
