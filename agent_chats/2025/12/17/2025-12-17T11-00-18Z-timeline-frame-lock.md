---
id: 2025-12-17T11-00-18Z-timeline-frame-lock
date: 2025-12-17T11:00:18Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, storyboard, timeline]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "When timeline exists, lock frames_per_scene input and default generation to timeline beat count."
---

## User Prompt
先做这个： 有时间轴时禁用帧数输入、默认使用 timeline 帧数

## Goals
- Prevent manual frame count input when an episode audio timeline exists.
- Use timeline beats as the default frame count for current scene generation.

## Changes
- Disabled “每场景分镜数” input when timeline is present; added helper text showing beat-derived frame count.
- Generate current scene now uses timeline beat count if available; generate-all skips overriding frame count when timeline exists (lets backend/time-beats decide).

## Validation
- `npm run lint` (frontend) — pass.

## Next Steps
- After登陆并生成时间轴，再试分镜生成，确认帧数锁定为 beats 数量；若需要全场景逐场映射 beats→frames，可进一步改后端/前端参数透传。

## Linked Commits
- (pending)
