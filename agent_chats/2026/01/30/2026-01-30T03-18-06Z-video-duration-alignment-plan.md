---
id: 2026-01-30T03-18-06Z-video-duration-alignment-plan
date: 2026-01-30T03:18:06Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, video, storyboard, planning]
related_paths:
  - tasks.md
summary: "Added phased tasks to align storyboard target durations with provider video duration constraints (e.g., Veo 4/6/8s)."
---

## User Prompt

现在的问题在于，视频生成模型可能能提供 6/8 秒的视频，不同视频模型的时长有区别，但是分镜可能会生成时间过长的分镜帧。怎么解决比较好？先更新 tasks.md，然后分步执行。

## Goals

- Make the duration mismatch problem explicit and actionable in `tasks.md`.
- Define a phased plan: capabilities abstraction + ceil-to-allowed + trim (P0), then storyboard split/merge (P1).
- Keep the change atomic and auditable.

## Changes

- Updated `tasks.md` with a new P0/P1 task group for aligning storyboard `target_duration_seconds` with provider allowed durations (Veo 4/6/8s), including trim and split/merge strategy.

## Validation

- `./docker/build_prod_images.sh` (tag=f6500d5)

## Next Steps

- Implement Phase 1 (capabilities + ceil-to-allowed + trim) and add unit tests.
- Run Docker E2E to validate a 5s storyboard frame produces a ~5s final MP4 while preserving the original ~6s provider output for auditing.

## Linked Commits

- chore(tasks): add plan for storyboard/video duration alignment
