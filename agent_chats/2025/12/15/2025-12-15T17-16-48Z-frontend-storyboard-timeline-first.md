---
id: 2025-12-15T17-16-48Z-frontend-storyboard-timeline-first
date: 2025-12-15T17:16:48Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, storyboard, timeline, dialogue-audio]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - tasks.md
summary: "Make storyboard page timeline-first: show per-frame time windows and add one-click sync from episode audio_timeline."
---

## User Prompt

分镜应该为时间轴服务。

## Goals

- 将 `audio_timeline` 作为事实来源：分镜页明确展示时间轴信息，并让分镜帧与时间窗对齐。
- 提供“从时间轴同步/重建分镜占位”的入口，避免分镜结构与音频 beats 脱节。

## Changes

- `ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`：
  - 在分镜页的时间轴卡片中新增「从时间轴同步分镜占位」按钮（支持 `overwrite_existing` 与 `pause` 阈值），直接调用后端 `/storyboard/from-audio-timeline/generate-async`。
  - 帧级 UI 展示时间窗 `start_ms/end_ms`（mm:ss.mmm），并将时长标记为“来自时间轴”（避免误以为分镜时长可脱离时间轴）。
  - 当检测到分镜占位基于旧的 `audio_timeline_version` 时，提示需要同步以保持对齐。
- `tasks.md`：更新分镜管理页与时间轴的对齐能力描述。

## Validation

- `cd ai-pic-frontend && npm run lint`
- Selenium（headless Chrome，替代 MCP DevTools：Transport closed）：
  - 登录 `geyunfei`，打开 `http://localhost:8089/episodes/10/storyboard?scriptId=17`
  - 校验页面存在「从时间轴同步分镜占位」按钮、帧卡片出现「时间轴:」与「来自时间轴」标记、episode 音频播放器可见

## Next Steps

- 若需要进一步强化“分镜为时间轴服务”的约束，可考虑：将 AI 结构生成与时间轴帧占位解耦（只允许在既有时间窗上做镜头语言补全），避免重新规划帧数导致与 timeline 不一致。

## Linked Commits

- pending
