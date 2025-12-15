---
id: 2025-12-15T16-37-47Z-e2e-episode-dialogue-audio-pipeline
date: 2025-12-15T16:37:47Z
participants: [human, codex]
models: [gpt-5.2]
tags: [e2e, dialogue-audio, timeline, storyboard]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - tasks.md
summary: "E2E validate episode dialogue audio → timeline → storyboard placeholder flow on episodes/10."
---

## User Prompt

整体完成该 Feature，并确保可以在 Episode 页面听到生成的对白音轨（所有音频上传 OSS）。

## Goals

- 在真实浏览器里跑通：scene 对白音轨 → episode 时间轴/拼接音轨 → 分镜帧占位。
- 记录关键任务与观察结果，便于回归与排查。

## Changes

- `tasks.md`：更新该 Feature 的验证描述为 Selenium headless Chrome 路径（MCP DevTools 当前 Transport closed）。

## Validation

- 环境：`http://localhost:8089/episodes/10`（登录账号 `geyunfei`）。
- Selenium（headless Chrome）验证路径：
  - 生成对白音轨任务 `task_id=263`：状态 `completed`（已有产物时跳过/复用）
  - 生成时间轴任务 `task_id=260`：状态 `completed`；生成 episode 级音频并写入 `episodes.extra_metadata.audio_timeline.episode_audio.oss_url`
  - 生成分镜帧占位：
    - `task_id=261`：首次因已有分镜且未勾选覆盖而失败（`storyboard_has_assets_refuse_overwrite`，提示清晰）
    - 勾选“覆盖分镜”后 `task_id=262`：状态 `completed`
  - 页面回填：可见 `audio[src*=episode-dialogue/scenes]` 与 `audio[src*=episode-dialogue/episodes]`，可直接播放 OSS 音频

## Next Steps

- 排查/修复 MCP Chrome DevTools “Transport closed”，恢复推荐的浏览器自测路径。

## Linked Commits

- pending
