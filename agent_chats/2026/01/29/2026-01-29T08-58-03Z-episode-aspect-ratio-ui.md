---
id: 2026-01-29T08-58-03Z-episode-aspect-ratio-ui
date: "2026-01-29T08:58:03Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, episode, storyboard, aspect-ratio]
related_paths:
  - ai-pic-frontend/src/components/features/episode/EpisodeAspectRatioSelect.tsx
  - ai-pic-frontend/src/components/features/episode/index.ts
  - ai-pic-frontend/src/components/features/index.ts
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - tasks.md
summary: "Add Episode aspect ratio selector to storyboard page (inherit story default or override to 9:16/16:9)."
---

## User Prompt

画幅只支持 9:16 / 16:9；默认 9:16；允许 Episode 层级设置默认值，并允许生成时临时覆盖。

## Goals

- 前端提供 Episode 级画幅设置入口（可继承 Story 默认）。
- 确保该设置对后续分镜视频生成的默认值可见、可复用。

## Changes

- `ai-pic-frontend/src/components/features/episode/EpisodeAspectRatioSelect.tsx`
  - 新增 Episode 画幅选择器：跟随故事 / 9:16（竖屏） / 16:9（横屏）。
  - 选择后调用 `episodeAPI.updateEpisode` 持久化到后端。
- `ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`
  - 在分镜页顶部工具条加入 `EpisodeAspectRatioSelect`。
- `ai-pic-frontend/src/components/features/episode/index.ts` + `ai-pic-frontend/src/components/features/index.ts`
  - 导出新组件，便于复用。
- `tasks.md`
  - P0-1 前端画幅设置任务标记完成（Story 默认 + Episode 覆盖 + 生成弹窗可临时覆盖）。

## Validation

- `cd ai-pic-frontend && npm run lint`（仅 warnings）
- `cd ai-pic-frontend && npm run build`
- `./docker/build_prod_images.sh`
- Chrome（MCP）E2E：
  - 登录 `http://localhost:8089/login`
  - 打开 `http://localhost:8089/episodes/131/storyboard`
  - 在页面顶部“画幅”选择器中切换到 `16:9（横屏）`，页面显示值更新为 `16:9（横屏）`

## Next Steps

- 补“验证：各生成 1 条 9:16 与 16:9 分镜视频，并用 ffprobe 校验”的验收步骤（`tasks.md` P0-1 最后一项）。

## Linked Commits

- (pending)

