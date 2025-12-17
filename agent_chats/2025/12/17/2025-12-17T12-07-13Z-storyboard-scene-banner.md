---
id: 2025-12-17T12-07-13Z-storyboard-scene-banner
date: 2025-12-17T12:07:13Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, storyboard]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Move storyboard scene nav to a top banner and scope audio/timeline to current scene"
---

## User Prompt

Storyboard页面需要：场景列表做顶部导航，选中后下方展示该场景时间轴与分镜，移除下方场景列表；对白音频展示当前场景的。

## Goals

- Provide a clear scene navigation banner at the top.
- Show only the selected scene’s timeline/frames, and scope the displayed audio clip to that scene.
- Remove the redundant bottom scene list.

## Changes

- Added a horizontal scene nav banner (from normalized scenes or frame fallback) to drive selection.
- Scoped the audio player to the current scene using media fragment of the episode audio based on timeline window; card title now reflects the scene.
- Removed the lower scene list; the frames panel now fills the width beneath the banner.

## Validation

- `npm run lint` (ai-pic-frontend): pass.

## Next Steps

- Reload storyboard page; select scenes via top banner to verify timeline/frames update and audio clip uses the scene window (HMR reload/restart may be needed).

## Linked Commits

- Pending
