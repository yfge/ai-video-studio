---
id: 2025-12-28T09-06-30Z-episode-page-redirect
date: "2025-12-28T09:06:30Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, routing, episode, storyboard]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
summary: "移除 /episodes/[id] 旧入口：统一重定向到 workspace，并修正分镜页返回地址"
---

## User Prompt

去掉 `http://localhost:8089/episodes/<episodeId>` 这个页面的入口；从分镜管理页返回剧集应返回到 `.../workspace?tab=storyboard&scriptId=58`。

## Goals

- `/episodes/[id]` 不再作为可达入口，统一跳转到 `/episodes/[id]/workspace`。
- 分镜管理页「返回剧集」返回到 workspace 的 storyboard tab，并带上当前 scriptId。
- 清理脚本页等仍跳转到旧 `/episodes/[id]` 的入口。

## Changes

- 将 `ai-pic-frontend/src/app/episodes/[id]/page.tsx` 改为 server redirect：统一跳转到 `.../workspace?tab=...`（兼容 `action=generate-timeline` 时默认落到 timeline tab）。
- `ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx` 的 “生成时间轴” 不再跳转到旧 `/episodes/[id]`，改为切换 workspace 的 timeline tab。
- `ai-pic-frontend/src/app/scripts/[id]/page.tsx` 的 “返回剧集” 不再跳转到旧 `/episodes/[id]`，改为跳转到 `.../workspace?tab=script&scriptId=<id>`。

## Validation

- 前端：`cd ai-pic-frontend && npm run lint`（既有 warning，lint 通过）。
- Docker：`./docker/build_prod_images.sh` 构建通过。
- Chrome E2E（MCP）：
  - 访问 `http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7` 自动跳转到 `.../workspace?tab=overview`
  - 在分镜管理页 `.../storyboard?scriptId=58` 点击「返回剧集」跳转到 `.../workspace?tab=storyboard&scriptId=58`

## Next Steps

- 若仍有入口将用户导向 `/episodes/[id]`，继续统一为 workspace（例如其它列表/卡片点击行为）。
- 将 workspace 中 “生成时间轴/生成分镜” 行为进一步与流水线任务联动（可选）。

## Linked Commits

- (pending)
