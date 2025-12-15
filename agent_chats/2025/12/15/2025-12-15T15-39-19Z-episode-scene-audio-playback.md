---
id: 2025-12-15T15-39-19Z-episode-scene-audio-playback
date: 2025-12-15T15:39:19Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, audio, ux]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - tasks.md
summary: "Expose per-scene dialogue audio playback/download on the Episode detail page"
---

## User Prompt

“生成的对白音轨在哪里听？我之前生成成功了，并没有（在页面看到入口）地址：http://localhost:8089/episodes/10”

## Goals

- 让已生成的“场景对白混音音轨（每场景一条）”在 Episode 页面可直接播放/下载
- 降低“只生成了 scene 音轨但未生成 episode timeline”的困惑（episode 音频链接仅在生成时间轴后出现）

## Changes

- `ai-pic-frontend/src/app/episodes/[id]/page.tsx`：
  - 在「对白音轨与时间轴」面板新增“场景对白音轨（scene）”折叠区
  - 自动加载 `GET /api/v1/story-structure/scripts/{script_id}/scenes`，读取 `scene.metadata.dialogue_audio.oss_url`
  - 为每个 scene 渲染 `audio` 播放控件 + “打开”链接（新标签页）
- `tasks.md`：补记并勾选该前端播放入口完成项

## Validation

- MCP Chrome DevTools 仍返回 `Transport closed`，本次用 Playwright Chromium 做浏览器自测：
  - 打开 `http://localhost:8089/episodes/10`（注入 `localStorage.auth_token`）
  - 展开“场景对白音轨（scene）”折叠区，确认存在可播放的 `audio` 控件与 OSS URL
- 证据文件：`/tmp/ai-video-studio-e2e-scene-audio-1765813231335/episode-scene-audio.png`
- `npm run lint`（通过 pre-commit 钩子）

## Next Steps

- （可选）将“episode 音频（拼接后）”也增加内嵌 `audio` 播放器，避免只能点外链。

## Linked Commits

- (pending)
