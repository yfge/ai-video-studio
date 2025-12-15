---
id: 2025-12-15T16-32-13Z-frontend-episode-dialogue-audio-playback
date: 2025-12-15T16:32:13Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, ux, dialogue-audio]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - tasks.md
summary: "Make dialogue audio playback discoverable on episode detail page (auto-open scene list + episode audio player)."
---

## User Prompt

生成的对白音轨在哪里听？我之前生成成功了，并没有（http://localhost:8089/episodes/10）。

## Goals

- 在 Episode 详情页让“对白音轨试听”更可发现：无需额外展开/跳转即可看到并播放已生成的音轨。

## Changes

- `ai-pic-frontend/src/app/episodes/[id]/page.tsx`：
  - 当存在 episode 级音频 URL 时，直接渲染 `<audio controls>` 播放器。
  - 当场景对白音轨已生成时，默认展开“场景对白音轨（scene）”列表（`<details open>`）。
- `tasks.md`：补充并勾选该 UX 修复项。

## Validation

- `cd ai-pic-frontend && npm run lint`
- Selenium（headless Chrome，替代 MCP DevTools：Transport closed）：
  - 登录 `geyunfei` 并访问 `http://localhost:8089/episodes/10`
  - 校验“场景对白音轨（scene）”默认展开且可见 `audio[src*=episode-dialogue/scenes]`

## Next Steps

- 在生成 episode 时间轴后（产出 episode 级音频 URL），复验该播放器在真实数据下可直接播放。

## Linked Commits

- pending
