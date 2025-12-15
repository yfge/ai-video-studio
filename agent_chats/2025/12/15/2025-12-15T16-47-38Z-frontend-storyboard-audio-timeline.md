---
id: 2025-12-15T16-47-38Z-frontend-storyboard-audio-timeline
date: 2025-12-15T16:47:38Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, storyboard, timeline, dialogue-audio]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - tasks.md
summary: "Pass episode audio timeline context into storyboard page and show beats + episode audio player."
---

## User Prompt

http://localhost:8089/episodes/10/storyboard 分镜管理中需要有时间轴传入

## Goals

- 从 Episode 详情页进入分镜管理时保留当前剧本上下文（scriptId），避免时间轴与分镜脚本不匹配。
- 在分镜管理页展示 episode `audio_timeline`（beats/version + episode 音频播放器），便于以声音驱动的时间轴对齐分镜。

## Changes

- `ai-pic-frontend/src/app/episodes/[id]/page.tsx`：点击“分镜管理”跳转时附带 `?scriptId=...`。
- `ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`：
  - 读取 `scriptId` query param 并优先选中对应剧本。
  - 解析 `episode.extra_metadata.audio_timeline`（按 scriptId 过滤），展示 beats/version 与 episode 音频播放器。
- `tasks.md`：补充并勾选该前端改动。

## Validation

- `cd ai-pic-frontend && npm run lint`
- Selenium（headless Chrome，替代 MCP DevTools：Transport closed）：
  - 登录 `geyunfei`，进入 `http://localhost:8089/episodes/10` → 点击“分镜管理”
  - 断言跳转 URL 包含 `?scriptId=17`，且分镜页“当前剧本”选中同一 script
  - 分镜页可见 `audio[src*=episode-dialogue/episodes]`（episode 级音频播放器）

## Next Steps

- 若后续需要“从时间轴生成分镜帧占位/重跑”，可在分镜管理页补充对应任务入口与覆盖提示。

## Linked Commits

- pending
