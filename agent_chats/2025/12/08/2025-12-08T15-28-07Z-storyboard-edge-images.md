---
id: 2025-12-08T15-28-07Z-storyboard-edge-images
date: 2025-12-08T15:28:07Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, storyboard]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Allow selecting multiple env/character images to generate first/last storyboard frames and refresh to display results."
---

## User Prompt

在分镜管理中，生成图像可以可以选择多个图像，包括多个人物 IP的图像以及环境的图像，来生成分镜的首帧和尾帧，两个都生成或是只生成一个 ，实现这个功能，同时要可以展示 对应的生成的图像

## Goals

- Enable selecting multiple environment + character images to drive first/last frame generation per scene.
- Let users choose to generate first, last, or both frames.
- Refresh storyboard to surface the generated images in the UI.

## Changes

- Added an edge-frame modal to pick reference images (env + multi-role) and toggles for首帧/尾帧; wired generation to `generateStoryboardImages` with selected frame indexes and references.
- Refactored reference-image loading for reuse between per-frame modal and edge modal; added a delayed storyboard refresh after edge generation so new `image_url` displays in-frame.
- Kept existing per-frame modal intact while sharing the same reference loader.

## Validation

- Manual: opened `/episodes/8/storyboard`, confirmed normalized场景加载；打开“生成首尾帧图像”弹窗可选择环境+角色图、切换首帧/尾帧选项并提交；分镜卡片显示 `image_url` 预览后刷新。
- Automated tests not run (frontend change).

## Next Steps

- Consider polling until生成任务完成以自动更新图像，无需手动刷新。
- Expose首/尾帧索引和任务状态提示，避免用户反复点击。

## Linked Commits

- (pending)
